# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

from elections.models import Voter, Nominee, Candidate, Vote, get_current_election
from elections.forms import NomineeFormSet

def index(request):
    return HttpResponse("Under construction")


def _get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[-1]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip

def _validate_voter(request, end_field):
    """Returns: voter, election, denied_reason, denied_detail (all optional)."""
    # TODO: Deprecate use of token here; can auto-generate log-in tokens instead.
    token = request.GET.get("token")
    election = get_current_election()
    voter = None
    if not election:
        return voter, election, None, None
    now = timezone.now()
    if now > getattr(election, end_field, now):
        return None, None, None, None
    if token:
        try:
            voter = Voter.objects.get(token=token)
        except Voter.DoesNotExist:
            return None, election, "Bad Token", "Voter not found."
        if request.user.is_authenticated and voter.user != request.user:
            return None, election, "Bad Token", "Token is not for the logged in user."
        if voter.election != election:
            return None, election, "Bad Token", "URL is not for this election."
    elif request.user.is_authenticated: # logged in
        try:
            voter = Voter.objects.get(election=election, user=request.user)
        except Voter.DoesNotExist:
            return None, election, "Not a Registered Voter", None
    else:
        return None, election, "Must be logged in or have a token.", None
    return voter, election, None, None

@login_required
def vote(request):
    voter, election, denied, detail = _validate_voter(request, "vote_end")
    if not election:
        return render(request, 'elections/no_election.html', {'voter': voter})
    if denied:
        return render(request, 'elections/denied.html', {
            'election': election,
            'voter': voter,
            'reason': denied,
            'detail': detail,
        })
    if request.GET.get("_debug"):
        request.session["vote_debug"] = True
    elif "vote_debug" in request.session:
        del request.session["vote_debug"]
    if request.method == "POST" and not voter.has_voted:
        if not request.session.get("vote_debug", False):
            # TODO: I imagine this could all be moved to a formset
            for key, rank in request.POST.items():
                if rank and key.startswith("candidate-"): # Format: candidate-#
                    candidate_id = int(key.split("-", 1)[-1])
                    candidate = Candidate.objects.get(id=candidate_id)
                    Vote.objects.create(
                        voter=voter,
                        candidate=candidate,
                        rank=rank,
                        ip=_get_client_ip(request)
                    )
            voter.has_voted = True
            voter.save()
        request.session["extra_notification"] = "Ballot received, thank you!"
        return redirect("website:index")
    return render(request, 'elections/election.html', {
            'election': election,
            'voter': voter,
        })

@login_required
def nominate(request):
    voter, election, denied, detail = _validate_voter(request, "nomination_end")
    if not election:
        return render(request, 'elections/no_election.html', {
            'election': election,
            'voter': voter,
        })
    if denied:
        return render(request, 'elections/denied.html', {
            'election': election,
            'voter': voter,
            'reason': denied,
            'detail': detail,
        })
    context = {
        'form_title': 'Election Nomination',
        'tab_title': 'Election',
        'form_info': mark_safe(voter.election.nomination_introduction),
        'election': election
    }
    if request.method == "POST":
        formset = NomineeFormSet(request.POST, instance=voter)
        if formset.is_valid():
            formset.save()
            context['more_notifications'] = ["Nominees saved"]
        else: # errors
            context["formset"] = formset
            return render(request, 'elections/tabular.html', context)
    formset = NomineeFormSet(instance=voter)
    context["formset"] = formset
    return render(request, 'elections/tabular.html', context)
