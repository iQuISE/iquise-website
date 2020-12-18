# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.shortcuts import render
from django.template import Template, Context
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

from iquhack.models import Hackathon, Tier, Sponsor

# Taken from https://codegolf.stackexchange.com/questions/4707/outputting-ordinal-numbers-1st-2nd-3rd#answer-4712
ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

def format_date_range(start, stop):
    """Nicely format a date range without repeating month unless spans two.
    
    This ignores the year.

    Example: February 1st-2nd; January 30th-February 1st.
    """
    # Ad ordinal
    start_day = ordinal(start.day)
    start_day = start.strftime("%B %%s") % start_day

    stop_day = ordinal(stop.day)
    if start.month != stop.month:
        stop_day = stop.strftime("%B %%s") % stop_day
    return "%s-%s" % (start_day, stop_day)

# Create your views here.
def index(request, start_date=None):
    # TODO: prefetch_related. See:
    # https://stackoverflow.com/questions/23405871/django-prefetch-related-no-duplicates-with-intermediate-table
    available_hackathons = Hackathon.objects.filter(published=True)
    if start_date:
        start_date = [int(item) for item in start_date.split("-")] # Convert to list of ints: [2020, 12, 12]
        start_date = datetime.date(*start_date)
        try:
            hackathon = available_hackathons.get(start_date=start_date)
        except ObjectDoesNotExist:
            raise Http404
    else: # Most recent
        hackathon = available_hackathons.first()
        if not hackathon: # No hackathons are in the database yet
            raise Http404 # TODO: probably shouldn't raise a 404 here
    
    # Easier to format the date here than in the template
    formatted_event_date = format_date_range(hackathon.start_date, hackathon.end_date)
    
    # Prepare a template-friendly sponsor data: List of (tier, abs_height, (sponsors,)) tuples
    sponsors = []
    # It will be more efficient to go discover sponsors by tier rather than the other way around
    for tier in Tier.objects.all():
        logo_height = hackathon.logo_max_height * tier.logo_rel_size/100.0
        if logo_height >= 1: # Only add if greater than a pixel
            tier_sponsorships = hackathon.sponsorship_set.filter(tier=tier)
            if tier_sponsorships.count(): # Never use len on django querysets!
                # Finish calculating
                logo_side = hackathon.logo_max_side_margin * tier.logo_rel_size/100.0
                logo_bottom = hackathon.logo_max_bottom_margin * tier.logo_rel_size/100.0
                # Add to list (could consider wrapping up logo stuff in dict/dataclass)
                sponsors.append((tier, logo_height, logo_side, logo_bottom, tier_sponsorships))
    
    # Prepare an ordered rendered sections list
    sections = [] # (title, html_content)
    for section in hackathon.section_set.all():
        html_template = "{% load iquhack_extras %}\n" + section.content
        if section.template:
            html_template = "%s\n%s" %(section.template.content, html_template)
        attachments = {}
        for attachment in section.attachment_set.all():
            attachments[attachment.name] = attachment.file.url
        context = {
            "hackathon": hackathon,
            "formatted_event_date": formatted_event_date,
            "attachments": attachments,
        }
        html_content = Template(html_template).render(Context(context))
        sections.append((section.title, html_content))

    context.update({"sections": sections})
    return render(request, "iquhack/iquhack.html", context={
            "formatted_event_date": formatted_event_date,
            "hackathon": hackathon,
            "sponsors": sponsors,
            "platform_sponsors": hackathon.sponsorship_set.filter(platform=True),
            "sections": sections
        })
