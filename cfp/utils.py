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
from django.core.exceptions import ValidationError


def is_editable(proposal, user):
    return ((not proposal.scheduled) and
            ((proposal.proposer == user and proposal.status != 'A') or
             topiclead(user, proposal.topic)))


def linkify(blueprints):
    links = {}
    for bp in blueprints.split():
        (project, name) = bp.split('/')
        links[bp] = "https://blueprints.launchpad.net/%s/+spec/%s" \
                 % (project, name)
    return links


def topiclead(user, topic):
    return (user.username == topic.lead_username) or user.is_staff


def _is_valid_lp_name(value):
    return value.replace('-', '').isalnum()


def validate_bp(value):
    bps = value.split()
    for bp in bps:
        members = bp.split("/")
        if len(members) != 2:
            raise ValidationError(u'Blueprints should be specified under'
                                  ' the form project/blueprint-name')
        (project, bpname) = list(members)
        if not _is_valid_lp_name(project):
            raise ValidationError(u'Incorrect project name: %s' % project)
        if not _is_valid_lp_name(bpname):
            raise ValidationError(u'Incorrect blueprint name: %s' % bpname)
        f = urllib.urlopen("https://api.launchpad.net/devel/%s/+spec/%s"
                           % (project, bpname))
        f.close()
        if f.getcode() != 200:
            raise ValidationError(u'No such blueprint: %s/%s'
                                  ' -- did you create it on Launchpad ?'
                                  % (project, bpname))
