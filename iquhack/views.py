# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.shortcuts import render
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

from iquhack.models import Hackathon

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
    
    return render(request, "iquhack/iquhack.html", context={"hackathon":hackathon})
