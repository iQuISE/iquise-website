# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.shortcuts import render
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

from iquhack.models import Hackathon, Tier, Sponsor

# Create your views here.
def index(request, start_date=None):
    if start_date:
        start_date = [int(item) for item in start_date.split("-")] # Convert to list of ints: [2020, 12, 12]
        start_date = datetime.date(*start_date)
        try:
            hackathon = Hackathon.objects.get(start_date=start_date)
        except ObjectDoesNotExist:
            raise Http404
    else: # Most recent
        hackathon = Hackathon.objects.order_by("-start_date").first()
        if not hackathon: # No hackathons are in the database yet
            raise Http404 # TODO: probably shouldn't raise a 404 here
    
    # Prepare a template-friendly sponsor data: List of (tier, abs_height, (sponsors,)) tuples
    sponsors = []
    # It will be more efficient to go discover sponsors by tier rather than the other way around
    for tier in Tier.objects.order_by("index"):
        abs_logo_height = hackathon.logo_max_height * tier.logo_rel_height/100.0
        if abs_logo_height >= 1: # Only add if greater than a pixel
            tier_sponsors = Sponsor.objects.filter(hackathon=hackathon).filter(tier=tier)
            if tier_sponsors.count(): # Never use len on django querysets!
                sponsors.append((tier, abs_logo_height, tier_sponsors))

    return render(request, "iquhack/iquhack.html", 
        context={
            "hackathon": hackathon,
            "sponsors": sponsors,
        })
