# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import *

# Create your views here.

from django.http import HttpResponse

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

def detail(request, presentation_id):
    iquise = IQUISE.objects.all()
    if not iquise:
        iquise = None
    else:
        iquise = iquise[0] # There can only be one
    presentation = Presentation.objects.filter(id=presentation_id)
    template = loader.get_template('home/presentation.html')
    context = {
        'presentation': presentation[0],
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
