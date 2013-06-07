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


def full_description(slot):
    desc = ""
    if slot.description:
        desc = slot.description + "\n\n"
    desc += combined_description(slot)
    return desc


def htmlize(desc):
    return desc.replace('\n', '<br />')


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
