# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import Presentation
from .models import Person

# Create your views here.

from django.http import HttpResponse

def index(request):
    presentations = Presentation.objects.order_by('date')
    #presentations = [presentations[0], presentations[0], presentations[0], presentations[0], presentations[0], presentations[0]]
    template = loader.get_template('home/index.html')
    context = {
        'presentations': presentations,
    }
    return HttpResponse(template.render(context, request))

def detail(request, presentation_id):
    presentation = Presentation.objects.filter(id=presentation_id)
    template = loader.get_template('home/detail.html')
    context = {
        'presentation': presentation[0],
    }
    return HttpResponse(template.render(context, request))

def people(request):
    people = Person.objects.all()
    template = loader.get_template('home/people.html')
    context = {
        'people': people,
    }
    return HttpResponse(template.render(context, request))
