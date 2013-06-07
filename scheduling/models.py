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

from django.db import models

from odsreg.cfp.models import Proposal, Topic


class Room(models.Model):
    code = models.CharField(max_length=1, primary_key=True)
    name = models.CharField(max_length=40)

    class Meta:
        ordering = ['code']

    def __unicode__(self):
        return self.code


class Slot(models.Model):
    start_time = models.CharField(max_length=16)
    room = models.ForeignKey(Room)
    topic = models.ForeignKey(Topic)
    proposals = models.ManyToManyField(Proposal, blank=True, null=True)
    title = models.CharField(max_length=60, blank=True,
        verbose_name="Override title with",
        help_text="Default title is the title of the first proposal. You can"
                  " override this default with the above-provided title")
    description = models.TextField(blank=True,
        verbose_name="Preface description with",
        help_text='Text to preface the description of the session with. It'
                  ' will be followed by the following session descriptions:')

    class Meta:
        ordering = ["start_time"]

    def __unicode__(self):
        return "%s %s %s" % (self.topic.name, self.room.code, self.start_time)
