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
from django.db import models
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


def is_valid_lp_name(value):
    return value.replace('-', '').isalnum()


def validate_bp(value):
    bps = value.split()
    for bp in bps:
        members = bp.split("/")
        if len(members) != 2:
            raise ValidationError(u'Blueprints should be specified under'
                                  ' the form project/blueprint-name')
        (project, bpname) = list(members)
        if not is_valid_lp_name(project):
            raise ValidationError(u'Incorrect project name: %s' % project)
        if not is_valid_lp_name(bpname):
            raise ValidationError(u'Incorrect blueprint name: %s' % bpname)
        f = urllib.urlopen("https://api.launchpad.net/devel/%s/+spec/%s"
                           % (project, bpname))
        f.close()
        if f.getcode() != 200:
            raise ValidationError(u'No such blueprint: %s/%s'
                                  ' -- did you create it on Launchpad ?'
                                  % (project, bpname))


class Topic(models.Model):
    name = models.CharField(max_length=40)
    lead_username = models.CharField(max_length=40)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class Proposal(models.Model):
    STATUSES = (
                ('U', 'Unreviewed'),
                ('I', 'Incomplete'),
                ('A', 'Preapproved'),
                ('R', 'Refused'),
               )
    proposer = models.ForeignKey(User)
    title = models.CharField(max_length=50,
        help_text="The title of your proposed session. This is mandatory.")
    description = models.TextField(
        help_text="The detailed subject and goals for your proposed session. "
                  "This is mandatory.")
    topic = models.ForeignKey(Topic,
        help_text="The topic the session belongs in. Click 'Help' below"
                  " for more details. This is mandatory.")
    blueprints = models.CharField(max_length=400, blank=True,
        validators=[validate_bp],
        help_text="Links to Launchpad blueprints. "
                  "For example 'nova/accounting' would link to a nova "
                  "blueprint called 'accounting'. You can specify multiple "
                  "links, separated by spaces. This field is optional.")
    status = models.CharField(max_length=1, choices=STATUSES)
    scheduled = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_modified']

    def __unicode__(self):
        return self.title


class Comment(models.Model):
    proposal = models.ForeignKey(Proposal)
    posted_date = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User)
    content = models.TextField(verbose_name="Add your comment")

    class Meta:
        ordering = ['posted_date']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        exclude = ('proposal', 'posted_date', 'author')


class ProposalForm(ModelForm):
    class Meta:
        model = Proposal
        exclude = ('proposer', 'status', 'scheduled')


class ProposalEditForm(ModelForm):
    class Meta:
        model = Proposal
        exclude = ('topic', 'proposer', 'status', 'scheduled')


class ProposalReviewForm(ModelForm):
    class Meta:
        model = Proposal
        fields = ('status',)


class ProposalSwitchForm(ModelForm):
    class Meta:
        model = Proposal
        fields = ('topic',)
