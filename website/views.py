# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.edit import FormView
from django.http import HttpResponse, Http404
from django.template import loader, RequestContext
from django.contrib.auth.models import User
from django.utils import timezone
from .models import *
from .forms import *
# Note for Presentation, one can use Presentation.THEORY etc.
from datetime import timedelta
# Create your views here.

def handler404(request):
    return render(request, '404.html', status=404)

def basic_context(request):
    # No analytics if superuser
    if request.user.is_superuser:
        useAnalytics = False
    else:
        useAnalytics = request.GET.get('analytics','yes')
        useAnalytics = useAnalytics.lower() == 'yes'
    iquise = IQUISE.objects.all()
    if not iquise:
        iquise = None
    else:
        iquise = iquise[0] # There can only be one
    return {'iquise':iquise,'useAnalytics': useAnalytics}

def index(request):
    today = timezone.now()
    presentations = Presentation.objects.filter(date__gte=today).order_by('date')
    if presentations.count() > 1: # assures i will be set
        for i in range(1,presentations.count()):
            days_to_saturday = timedelta( (5-presentations[i-1].date.weekday()) % 7 )
            delta = presentations[i].date - (presentations[i-1].date+days_to_saturday)
            if delta.days > 7:
                i -= 1 # Failed, so "uncount" this one
                break # Up to next saturday
        presentations = presentations[0:i+1]
    template = loader.get_template('home/index.html')
    context = basic_context(request)
    context.update({
        'presentations': presentations,
    })
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
