# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.exceptions import PermissionDenied

from elections.models import Voter, Nominee, get_current_election
from elections.forms import NomineeFormSet

def index(request):
    return HttpResponse("Under construction")

def nominate(request):
    token = request.GET.get("token")
    election = get_current_election()
    voter = None
    if not election:
        raise Http404()
    # TODO: more info on why permission denied. not logged in, bad token etc.
    if timezone.now() > election.nomination_end:
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
            return render(request, 'forms/tabular.html', context)
    formset = NomineeFormSet(instance=voter)
    context["formset"] = formset
    return render(request, 'elections/tabular.html', context)
