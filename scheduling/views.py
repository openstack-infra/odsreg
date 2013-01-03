# Copyright 2011 Thierry Carrez <thierry@openstack.org>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import urllib
import urllib2

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.encoding import smart_str
from odsreg.cfp.models import Proposal, Topic
from odsreg.cfp.views import topiclead, forbidden
from odsreg.scheduling.models import Slot, SlotForm


def combined_id(slot):
    return slot.proposals.order_by('id')[0].id


def combined_title(slot):
    if slot.title:
        return slot.title
    proposals = slot.proposals.all()
    if len(proposals) > 0:
        return proposals[0].title
    return ""


def combined_description(slot):
    full_desc = ""
    proposals = slot.proposals.all()
    if len(proposals) > 1 or slot.title:
        full_desc = "This session will include the following subject(s):\n\n"
    for p in slot.proposals.all():
        if len(proposals) > 1 or slot.title:
            full_desc = full_desc + p.title + ":\n\n"
        full_desc = full_desc + p.description + "\n\n"
        full_desc += "(Session proposed by %s %s)\n\n" % (
            p.proposer.first_name, p.proposer.last_name)
    return full_desc


def htmlize(desc):
    return desc.replace('\n', '<br />')


def full_description(slot):
    desc = ""
    if slot.description:
        desc = slot.description + "\n\n"
    desc += combined_description(slot)
    return desc


def scheduling(request, topicid):
    topic = Topic.objects.get(id=topicid)
    if not topiclead(request.user, topic):
        return forbidden()
    if request.method == 'POST':
        action = request.POST['action']
        proposal = Proposal.objects.get(id=request.POST['proposal'])
        slot = Slot.objects.get(id=request.POST['slot'])
        already_scheduled = slot.proposals.all()
        if action == "add":
            if proposal not in already_scheduled:
                slot.proposals.add(proposal)
                slot.save()
                proposal.scheduled = True
                proposal.save()
        if action == "del":
            if proposal in already_scheduled:
                if len(already_scheduled) == 1:
                    slot.title = ""
                    slot.description = ""
                slot.proposals.remove(proposal)
                slot.save()
                proposal.scheduled = False
                proposal.save()
    accepted = Proposal.objects.filter(status='A', scheduled=False,
                                       topic=topic)
    schedule = Slot.objects.filter(topic=topic)
    return render(request, "scheduling.html",
                  {'accepted': accepted,
                   'schedule': schedule,
                   'topic': topic})


def end_time(start_time):
    """Rough calculation of end time.
       Works because we don't start at 08:00 and align on 10's of minutes"""
    end_minute = int(start_time[-2:]) + 40
    if end_minute >= 60:
        end_hour = str(int(start_time[-5:-3]) + 1)
        end_minute = end_minute - 60
        if end_minute == 0:
            return start_time[:-5] + end_hour + ":00"
        else:
            return start_time[:-5] + end_hour + ":" + str(end_minute)
    else:
        return start_time[:-2] + str(end_minute)


def publish(request, topicid):
    topic = Topic.objects.get(id=topicid)
    if not topiclead(request.user, topic):
        return forbidden()
    list_calls = ""
    baseurl = "http://%s.sched.org/api/session/" % settings.SCHED_URL
    for slot in Slot.objects.filter(topic=topicid):
        if len(slot.proposals.all()) > 0:
            values = {'api_key': settings.SCHED_API_KEY,
                      'session_key': "slot-%d" % combined_id(slot),
                      'name': smart_str(combined_title(slot)),
                      'session_start': slot.start_time,
                      'session_end': end_time(slot.start_time),
                      'session_type': 'Design Summit',
                      'session_subtype': slot.topic,
                      'venue': slot.room.name,
                      'description': htmlize(smart_str(
                                              full_description(slot)))}
            data = urllib.urlencode(values)
            if settings.SCHED_API_KEY == "getThisFromSched":
                list_calls += "%s<P>" % data
            else:
                f = urllib2.urlopen(baseurl + "mod", data)
                if f.readline().startswith("ERR:"):
                    f.close()
                    f = urllib2.urlopen(baseurl + "add", data)
                    f.close()
    return render(request, "sched.html",
                  {'list_calls': list_calls,
                   'topic': topic})


def edit(request, slotid):
    slot = Slot.objects.get(id=slotid)
    if not topiclead(request.user, slot.topic):
        return forbidden()
    if request.method == 'POST':
        form = SlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/scheduling/%s' % slot.topic.id)
    else:
        form = SlotForm(instance=slot)
    return render(request, 'slotedit.html',
                  {'form': form,
                   'title': combined_title(slot),
                   'full_desc': combined_description(slot),
                   'slot': slot})


def swap(request, slotid):
    oldslot = Slot.objects.get(id=slotid)
    if not topiclead(request.user, oldslot.topic):
        return forbidden()
    if request.method == 'POST':
        newslotid = int(request.POST['newslotid'])
        newslot = Slot.objects.get(id=newslotid, topic=oldslot.topic)
        new_start_time = newslot.start_time
        new_room = newslot.room
        newslot.start_time = oldslot.start_time
        newslot.room = oldslot.room
        oldslot.start_time = new_start_time
        oldslot.room = new_room
        newslot.save()
        oldslot.save()
        return HttpResponseRedirect('/scheduling/%s' % oldslot.topic.id)

    newslots = []
    available_slots = Slot.objects.filter(
                          topic=oldslot.topic).exclude(id=slotid)
    for slot in available_slots:
        triplet = (slot.start_time, slot.id, combined_title(slot))
        newslots.append(triplet)
    return render(request, 'slotswap.html',
                  {'title': combined_title(oldslot),
                   'oldslot': oldslot,
                   'newslots': newslots})


def graph(request, topicid):
    topic = Topic.objects.get(id=topicid)
    unsched_proposals = Proposal.objects.filter(topic=topic, scheduled=False)
    slots = Slot.objects.filter(topic=topic)
    nbscheduled = 0
    nbavail = 0
    for slot in slots:
        nbavail = nbavail + 1
        if len(slot.proposals.all()) > 0:
            nbscheduled = nbscheduled + 1
    stats = {'U': 0, 'I': 0, 'A': 0,
             'S': nbscheduled,
             'avail': nbavail}
    nbproposed = 0
    for proposal in unsched_proposals:
        if proposal.status != 'R':
            stats[proposal.status] += 1
            nbproposed += 1
    stats['max'] = max(stats['avail'], nbproposed + nbscheduled)

    return render(request, "graph.html", {'stats': stats, 'topic': topic})
