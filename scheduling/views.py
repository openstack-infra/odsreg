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

from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.template.response import TemplateResponse
from django.utils.encoding import smart_str
from odsreg.cfp.models import Proposal, Topic, Event
from odsreg.cfp.utils import topiclead
from odsreg.scheduling.forms import SlotForm
from odsreg.scheduling.models import Slot
from odsreg.scheduling.utils import combined_id, combined_title
from odsreg.scheduling.utils import combined_description, full_description
from odsreg.scheduling.utils import htmlize, end_time


def scheduling(request, topicid):
    topic = Topic.objects.get(id=topicid)
    if not topiclead(request.user, topic):
        return HttpResponseForbidden("Forbidden")
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
    return TemplateResponse(request, "scheduling.html",
                            {'accepted': accepted,
                             'schedule': schedule,
                             'topic': topic})


def publish(request, topicid):
    event = Event.objects.get(status__in=['A', 'C'])
    topic = Topic.objects.get(id=topicid)
    if not topiclead(request.user, topic):
        return HttpResponseForbidden("Forbidden")
    list_calls = ""
    baseurl = "http://%s.sched.org/api/session/" % event.sched_url
    for slot in Slot.objects.filter(topic=topicid):
        if len(slot.proposals.all()) > 0:
            values = {'api_key': event.sched_api_key,
                      'session_key': "slot-%d" % combined_id(slot),
                      'name': smart_str(combined_title(slot)),
                      'session_start': slot.start_time,
                      'session_end': end_time(slot.start_time),
                      'session_type': slot.topic,
                      'venue': slot.room.name,
                      'description': htmlize(smart_str(
                                              full_description(slot)))}
            data = urllib.urlencode(values)
            if not event.sched_api_key:
                list_calls += "%s<P>" % data
            else:
                f = urllib2.urlopen(baseurl + "mod", data)
                if f.readline().startswith("ERR:"):
                    f.close()
                    f = urllib2.urlopen(baseurl + "add", data)
                    f.close()
    return TemplateResponse(request, "sched.html",
                            {'list_calls': list_calls,
                             'topic': topic})


def edit(request, slotid):
    slot = Slot.objects.get(id=slotid)
    if not topiclead(request.user, slot.topic):
        return HttpResponseForbidden("Forbidden")
    if request.method == 'POST':
        form = SlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/scheduling/%s' % slot.topic.id)
    else:
        form = SlotForm(instance=slot)
    return TemplateResponse(request, 'slotedit.html',
                            {'form': form,
                             'title': combined_title(slot),
                             'full_desc': combined_description(slot),
                             'slot': slot})


def swap(request, slotid):
    oldslot = Slot.objects.get(id=slotid)
    if not topiclead(request.user, oldslot.topic):
        return HttpResponseForbidden("Forbidden")
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
    return TemplateResponse(request, 'slotswap.html',
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

    return TemplateResponse(request, "graph.html",
                            {'stats': stats,
                             'topic': topic})
