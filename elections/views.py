# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.exceptions import PermissionDenied

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
    token = request.GET.get("token")
    election = get_current_election()
    voter = None
    if not election:
        raise Http404()
    # TODO: more info on why permission denied. not logged in, bad token etc.
    now = timezone.now()
    if now > getattr(election, end_field, now):
        raise PermissionDenied()
    try:
        if token:
            # TODO: maybe check if also logged in that users match
            voter = Voter.objects.get(token=token)
            if voter.election != election:
                raise PermissionDenied()
        elif request.user.is_authenticated: # logged in
            voter = Voter.objects.get(election=election, user=request.user)
    except Voter.DoesNotExist:
        raise PermissionDenied()
    if not voter:
        raise PermissionDenied()
    return voter, election

def vote(request):
    voter, election = _validate_voter(request, "vote_end")
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

def nominate(request):
    voter, election = _validate_voter(request, "nomination_end")
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
            context['notifications'] = ["Nominees saved"]
        else: # errors
            context["formset"] = formset
            return render(request, 'elections/tabular.html', context)
    formset = NomineeFormSet(instance=voter)
    context["formset"] = formset
    return render(request, 'elections/tabular.html', context)
