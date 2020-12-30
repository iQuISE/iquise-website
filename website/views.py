# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, Http404
from django.template import loader
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import render

from website.models import *
from iquise.utils import basic_context

def handler404(request):
    return render(request, '404.html', status=404)

def index(request):
    presentations = []
    today = timezone.localtime()
    session = Session.active_session()
    notification = None
    if session: # Current session is the one that hasn't ended and has the earliest start date
        events = session.event_set.filter(date__gte=today-timedelta(days=1)).order_by('date')
        for event in events:
            pres_confirmed = event.presentation_set.filter(confirmed=True)
            assert pres_confirmed.count() <= 1, Exception('More than 1 presentation confirmed for event: %s'%event)
            if pres_confirmed.count() == 1:
                if not pres_confirmed[0].event.first().cancelled: # Don't display the talk if cancelled
                    presentations.append(pres_confirmed[0])
                if pres_confirmed[0].event.first().date.date() == today.date():
                    # If there are two talks the same day, only display cancelled as last resort
                    if pres_confirmed[0].event.first().cancelled:
                        if not notification:
                            notification = 'Event Cancelled Today'
                    else:
                        url = reverse('website:presentation',args=[pres_confirmed[0].id])
                        notification = mark_safe('<a href="%s">Event Today! %s</a>'%(url,pres_confirmed[0].event.first().location))
            else: break # Empty event means we stop displaying presentations
    template = loader.get_template('home/index.html')
    context = basic_context(request)
    context.update({
        'presentations': presentations,
        'session': session,
    })
    if notification:
        context['notifications'].append(notification)
    return HttpResponse(template.render(context,request))

def presentation(request, presentation_id):
    try:
        presentation = Presentation.objects.get(id=presentation_id)
    except:
        raise Http404
    template = loader.get_template('home/presentation.html')
    context = basic_context(request)
    context.update({
        'presentation': presentation,
    })
    return HttpResponse(template.render(context,request))

def archive(request):
    future_events = Event.objects.filter(date__gte = timezone.localtime()).exclude(event__cancelled=True) # This will hopefully be smaller than past events in long term
    cancelled_events = Events.objects.filter(cancelled=True) # Filter out cancelled events so they're not displayed in the archive 
    presentations = Presentation.objects.filter(confirmed=True).exclude(event__in=future_events).exclude(event__in=cancelled_events) \
        .prefetch_related('event','presenters','event__session') # Reduce db queries to a single run (optimizes template render)
    template = loader.get_template('home/archive.html')
    context = basic_context(request)
    context.update({
        'presentations': presentations,
    })
    return HttpResponse(template.render(context,request))

@staff_member_required
def scheduler(request):
    template = loader.get_template('forms/scheduler.html')
    context = basic_context(request)
    context.update({

    })
    return HttpResponse(template.render(context,request))
