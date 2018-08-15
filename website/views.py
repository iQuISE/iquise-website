# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.edit import FormView
from django.http import HttpResponse, Http404
from django.template import loader, RequestContext
from django.contrib.auth.models import User
from .models import *
from .forms import *
# Note for Presentation, one can use Presentation.THEORY etc.

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
    presentations = Presentation.objects.order_by('date')
    #presentations = [presentations[0], presentations[0], presentations[0], presentations[0], presentations[0], presentations[0]]
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
