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

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth import logout
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils.encoding import smart_str

from odsreg.cfp.models import Proposal, Topic, Comment
from odsreg.cfp.forms import ProposalForm, ProposalEditForm, CommentForm
from odsreg.cfp.forms import ProposalReviewForm, ProposalSwitchForm
from odsreg.cfp.utils import linkify, is_editable, topiclead


@login_required
def list(request):
    proposals = Proposal.objects.all()
    reviewable_topics = Topic.objects.filter(
        lead_username=request.user.username)
    request.session['lastlist'] = ""
    return render(request, "cfplist.html",
                  {'proposals': proposals,
                   'reviewable_topics': reviewable_topics})


@login_required
def topiclist(request, topicid):
    topic = Topic.objects.get(id=topicid)
    if not topiclead(request.user, topic):
        return HttpResponseForbidden("Forbidden")
    proposals = Proposal.objects.filter(topic=topicid)
    request.session['lastlist'] = "cfp/topic/%s" % topicid
    return render(request, "topiclist.html",
                  {'proposals': proposals,
                   'topic': topic})


@login_required
def topicstatus(request):
    topics = Topic.objects.all()
    return render(request, "topicstatus.html", {'topics': topics})


@login_required
def create(request):
    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.proposer = request.user
            proposal.status = 'U'
            proposal.save()
            return list(request)
    else:
        form = ProposalForm()

    topics = Topic.objects.all()
    return render(request, 'cfpcreate.html', {'topics': topics, 'form': form})


@login_required
def details(request, proposalid):
    proposal = Proposal.objects.get(id=proposalid)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.proposal = proposal
            comment.author = request.user
            comment.save()
    else:
        form = CommentForm()
    comments = Comment.objects.filter(proposal=proposal)
    return render(request, "cfpdetails.html",
                  {'proposal': proposal,
                   'form': form,
                   'comments': comments,
                   'editable': is_editable(proposal, request.user),
                   'blueprints': linkify(proposal.blueprints)})


@login_required
def edit(request, proposalid):
    proposal = Proposal.objects.get(id=proposalid)
    if not is_editable(proposal, request.user):
        return HttpResponseForbidden("Forbidden")
    if request.method == 'POST':
        form = ProposalEditForm(request.POST, instance=proposal)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/%s' % request.session['lastlist'])
    else:
        form = ProposalEditForm(instance=proposal)
    return render(request, 'cfpedit.html', {'form': form,
                                            'proposal': proposal})


@login_required
def delete(request, proposalid):
    proposal = Proposal.objects.get(id=proposalid)
    if ((proposal.proposer != request.user) or proposal.status in ['A', 'S']):
        return HttpResponseForbidden("Forbidden")
    if request.method == 'POST':
        proposal.delete()
        return HttpResponseRedirect('/%s' % request.session['lastlist'])
    return render(request, 'cfpdelete.html', {'proposal': proposal})


@login_required
def switch(request, proposalid):
    proposal = Proposal.objects.get(id=proposalid)
    if ((proposal.proposer != request.user)
      and not topiclead(request.user, proposal.topic)) or proposal.scheduled:
        return HttpResponseForbidden("Forbidden")
    if request.method == 'POST':
        form = ProposalSwitchForm(request.POST, instance=proposal)
        if form.is_valid():
            form.save()
            proposal = Proposal.objects.get(id=proposalid)
            proposal.status = 'U'
            proposal.save()
            return HttpResponseRedirect('/%s' % request.session['lastlist'])
    else:
        form = ProposalSwitchForm(instance=proposal)
    return render(request, 'cfpswitch.html', {'form': form,
                                              'proposal': proposal})


@login_required
def review(request, proposalid):
    proposal = Proposal.objects.get(id=proposalid)
    if not topiclead(request.user, proposal.topic):
        return HttpResponseForbidden("Forbidden")
    current_status = proposal.status
    status_long = proposal.get_status_display()
    if request.method == 'POST':
        form = ProposalReviewForm(request.POST, instance=proposal)
        if form.is_valid():
            form.save()
            reviewer_notes = ''
            if form.cleaned_data['comment']:
                reviewer_notes = form.cleaned_data['comment']
                c = Comment()
                c.proposal = proposal
                c.author = request.user
                c.content = reviewer_notes
                c.save()
            if (settings.SEND_MAIL and current_status != proposal.status):
                lead = User.objects.get(username=proposal.topic.lead_username)
                if (lead.email and proposal.proposer.email):
                    message = """
This is an automated email.
If needed, you should reply directly to the topic lead (%s).

On your session proposal: %s
The topic lead (%s) changed status from %s to %s.

Reviewer's notes:
%s

You can edit your proposal at: %s/cfp/edit/%s""" \
                        % (proposal.topic.lead_username,
                           smart_str(proposal.title),
                           proposal.topic.lead_username,
                           status_long, proposal.get_status_display(),
                           smart_str(reviewer_notes),
                           settings.SITE_ROOT, proposalid)
                email = EmailMessage(settings.EMAIL_PREFIX +
                         "Status change on your session proposal",
                         message, settings.EMAIL_FROM,
                         [proposal.proposer.email, ], [],
                         headers={'Reply-To': lead.email})
                email.send()
            return HttpResponseRedirect('/cfp/topic/%d' % proposal.topic.id)
    else:
        form = ProposalReviewForm(instance=proposal)
    comments = Comment.objects.filter(proposal=proposal)
    return render(request, 'cfpreview.html',
                  {'form': form,
                   'proposal': proposal,
                   'comments': comments,
                   'blueprints': linkify(proposal.blueprints)})


def dologout(request):
    logout(request)
    return HttpResponseRedirect('/')
