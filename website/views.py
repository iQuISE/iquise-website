# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
from .models import *

# Create your views here.

from django.http import HttpResponse

def handler404(request):
    return render(request, '404.html', status=404)

def index(request):
    iquise = IQUISE.objects.all()
    if not iquise:
        iquise = None
    else:
        iquise = iquise[0] # There can only be one
    presentations = Presentation.objects.order_by('date')
    #presentations = [presentations[0], presentations[0], presentations[0], presentations[0], presentations[0], presentations[0]]
    template = loader.get_template('home/index.html')
    context = {
        'presentations': presentations,
        'iquise' : iquise,
    }
    return HttpResponse(template.render(context, request))

def presentation(request, presentation_id):
    iquise = IQUISE.objects.all()
    if not iquise:
        iquise = None
    else:
        iquise = iquise[0] # There can only be one
    try:
        presentation = Presentation.objects.get(id=presentation_id)
    except:
        raise Http404
    template = loader.get_template('home/presentation.html')
    context = {
        'presentation': presentation,
        'iquise' : iquise,
    }
    return HttpResponse(template.render(context, request))

def people(request):
    iquise = IQUISE.objects.all()
    if not iquise:
        iquise = None
    else:
        iquise = iquise[0] # There can only be one
    people = Person.objects.all()
    template = loader.get_template('home/people.html')
    context = {
        'people': people,
        'iquise' : iquise,
    }
    return HttpResponse(template.render(context, request))
