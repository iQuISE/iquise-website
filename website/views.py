# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.edit import FormView
from django.http import HttpResponse, Http404
from django.template import loader, RequestContext
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.conf import settings
from .models import *
from .forms import *
# Note for Presentation, one can use Presentation.THEORY etc.
from datetime import timedelta
# Create your views here.

def handler404(request):
    return render(request, '404.html', status=404)

def basic_context(request):
    notifications = []
    if settings.DEBUG:
        notifications = ['DEVELOPMENT SERVER']
    # No analytics if superuser
    if request.user.is_superuser:
        useAnalytics = False
    else:
        useAnalytics = not settings.DEBUG
    iquise = IQUISE.objects.all().first() # Returns none if doesn't exist
    donors = [str(d) for d in Donor.objects.all()]
    return {'iquise':iquise,'useAnalytics': useAnalytics,'notifications':notifications,'donors':donors}

def index(request):
    presentations = []
    today = timezone.now()
    session = Session.acvite_session()
    notification = None
    if session: # Current session is the one that hasn't ended and has the earliest start date
        events = session.event_set.all().order_by('date')
        for event in events:
            pres_confirmed = event.presentation_set.filter(confirmed=True)
            assert pres_confirmed.count() <= 1, Exception('More than 1 presentation confirmed for event: %s'%event)
            if pres_confirmed.count() == 1:
                presentations.append(pres_confirmed[0])
                if pres_confirmed[0].event.date.date() == today.date():
                    if pres_confirmed[0].event.cancelled:
                        notification = 'Talk Cancelled Today'
                    else:
                        url = reverse('website:presentation',args=[pres_confirmed[0].id])
                        notification = mark_safe('<a href="%s">Talk Today! %s</a>'%(url,pres_confirmed[0].event.location))
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

def people(request):
    people = User.objects.all().filter(is_superuser=False) # Filter "iquise"
    template = loader.get_template('home/people.html')
    context = basic_context(request)
    context = ({
        'people': people,
    })
    return HttpResponse(template.render(context,request))

class join(FormView):
    template_name = 'home/join.html'
    form_class = PersonForm
    success_url = '/'

    def form_valid(self,form):
        form.join_method = Person.WEBSITE
        form.save()
        return super(join, self).form_valid(form)
