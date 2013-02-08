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

import json

from django.core.management.base import BaseCommand, CommandError
from scheduling.models import Slot, Room
from cfp.models import Topic


class Command(BaseCommand):
    args = '<description.json>'
    help = 'Create slots from JSON description'

    def handle(self, *args, **options):

        if len(args) != 1:
            raise CommandError('Incorrect arguments')

        try:
            with open(args[0]) as f:
                data = json.load(f)
        except ValueError as exc:
            raise CommandError("Malformed JSON: %s" % exc.message)

        def slot_generator(mydata):
            for d in mydata['slots']:
                for h in d['hours']:
                    yield (d['day'], h)

        for roomcode, roomdesc in data['rooms'].iteritems():
            r = Room(code=roomcode, name=roomdesc)
            r.save()

        for topicname, desc in data['topics'].iteritems():
            started = False
            t = Topic.objects.get(name=topicname)
            room = Room.objects.get(code=desc['room'])
            for (d, h) in slot_generator(data):
                if (d == desc['start_day'] and h == desc['first_slot']):
                    started = True
                if started:
                    s = Slot(start_time="%s %s" % (d, h), room=room, topic=t)
                    s.save()
                if (d == desc['end_day'] and h == desc['last_slot']):
                    break
