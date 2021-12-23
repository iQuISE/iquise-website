# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import StringIO

from django.shortcuts import render, redirect
from django.template import Template, Context
from django.http import Http404, HttpResponse
from django.urls import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import FormView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test

from iquhack.models import Application, Hackathon, Tier, Sponsor
from iquhack.forms import AppForm

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

def get_hackathon_from_datestr(start_date, available_hackathons = None):
    available_hackathons = available_hackathons or Hackathon.objects.filter(published=True)
    start_date = [int(item) for item in start_date.split("-")] # Convert to list of ints: [2020, 12, 12]
    start_date = datetime.date(*start_date)
    try:
        return available_hackathons.get(start_date=start_date)
    except ObjectDoesNotExist:
        raise Http404

# Create your views here.
def index(request, start_date=None):
    # TODO: prefetch_related. See:
    # https://stackoverflow.com/questions/23405871/django-prefetch-related-no-duplicates-with-intermediate-table
    available_hackathons = Hackathon.objects.filter(published=True)
    if start_date:
        hackathon = get_hackathon_from_datestr(start_date, available_hackathons)
    else: # Most recent
        hackathon = available_hackathons.first()
        if not hackathon: # No hackathons are in the database yet
            raise Http404 # TODO: probably shouldn't raise a 404 here
        # Redirect so any refs to the URL work permanently
        return redirect('iquhack:hackathon', hackathon.start_date, permanent=False)
    last_hackathon = Hackathon.objects.filter(published=True, start_date__lt=hackathon.start_date).first()

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

    return render(request, "iquhack/iquhack.html", context={
            "formatted_event_date": formatted_event_date,
            "hackathon": hackathon,
            "sponsors": sponsors,
            "platform_sponsors": hackathon.sponsorship_set.filter(platform=True),
            "sections": sections,
            "last_hackathon": last_hackathon,
        })

class AppView(FormView):
    template_name = 'iquhack/app.html'
    form_class = AppForm
    success_url = reverse_lazy("members:profile")

    def get_context_data(self, **kwargs):
        context = super(AppView, self).get_context_data(**kwargs)
        context['form_title'] = 'iQuHACK Application'
        context['tab_title'] = 'iQuHACK App'
        return context
        
    def get_form_kwargs(self):
        form_kw = super(AppView, self).get_form_kwargs()
        hackathon = get_hackathon_from_datestr(self.kwargs["start_date"])
        if not hackathon.open: # shouldn't ever get here but just in case
            raise Http404("Application period not open.")

        if not hackathon.app_questions:
            raise ValueError("This hackathon doesn't have questions configured.")
        form_kw["user"] = self.request.user
        form_kw["hackathon"] = hackathon
        return form_kw

    def dispatch(self, request, *args, **kwargs):
        if not get_hackathon_from_datestr(self.kwargs["start_date"]).open:
            self.request.session["extra_notification"] = "Application period not open."
            return redirect("iquhack:index")
        # This is a bit awkward in conjunction with login_required decorators since
        # we're preempting it. When accessing join form with the intent of registering
        # for iquhack, we want to allow more emails which means we should turn off
        # our default subscription which requires uni emails.
        if not self.request.user.is_authenticated:
            self.request.session["join:no_default_subs"] = True
        return super(AppView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return super(AppView, self).form_valid(form)

    @method_decorator(login_required)
    def get(self, *args, **kw):
        return super(AppView, self).get(*args, **kw)

    @method_decorator(login_required)
    def post(self, *args, **kw):
        return super(AppView, self).post(*args, **kw)

    @method_decorator(login_required)
    def put(self, *args, **kw):
        return super(AppView, self).put(*args, **kw)

def is_iquhack_member(user):
    return user.is_superuser or user.groups.filter(name="iQuHACK").exists()

@user_passes_test(is_iquhack_member)
def all_apps_view(request, start_date):
    hackathon = get_hackathon_from_datestr(start_date)
    # header, rows = hackathon.get_apps()
    raw_apps = Application.objects.filter(hackathon=hackathon)
    return render(request, "iquhack/view_apps.html", context={
            "hackathon": hackathon,
            "questions": [],
            "responses": [],
            "raw_apps": raw_apps,
        })

@user_passes_test(is_iquhack_member)
def all_apps_download(request, start_date):
    hackathon = get_hackathon_from_datestr(start_date)
    header, rows = hackathon.get_apps()

    output = StringIO.StringIO()
    write_csv_rows(output, [header]+rows)
    output.seek(0) # Rewind file
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename="iquhack_apps.csv"'
    return response

def write_csv_rows(stream, rows, delim=","):
    # Python 2.7's csv writer doesn't do utf8!
    for row in rows:
        fmted_row = []
        for cell in row:
            if isinstance(cell, datetime.datetime):
                cell = cell.isoformat()
            elif isinstance(cell, list):
                cell = u", ".join(cell)
            else:
                cell = unicode(cell)
            fmted_row.append('"%s"'%cell.replace(u'"', u'""')) # Escape quote with dbl quote
        rowstr = delim.join(fmted_row)+"\n"
        stream.write(rowstr)