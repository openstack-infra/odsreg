# Copyright 2013 Thierry Carrez <thierry@openstack.org>
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

from django.shortcuts import render

from odsreg.cfp.models import Event


class EventMiddleware():

    def process_request(self, request):
        # Check that we have an event available, return canned page if we don't
        events = Event.objects.filter(status__in=['A', 'C'])
        if events.count() != 1:
            return render(request, "noevent.html")
        else:
            self.event = events[0]
            return None

    def process_template_response(self, request, response):
        # Add event to the response context
        response.context_data['event'] = self.event
        return response
