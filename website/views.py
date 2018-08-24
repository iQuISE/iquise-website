# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms.formsets import formset_factory
from django.views.generic.edit import FormView
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader, RequestContext
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.conf import settings
from .models import *
from .forms import *
# Note for Presentation, one can use Presentation.THEORY etc.
from datetime import timedelta
import pytz
# Create your views here.
import hashlib, zlib
import cPickle as pickle
import urllib

def encode_data(data):
    """Turn `data` into a hash and an encoded string, suitable for use with `decode_data`."""
    text = zlib.compress(pickle.dumps(data, 0)).encode('base64').replace('\n', '')
    m = hashlib.md5(settings.SECRET_KEY + text).hexdigest()[:12]
    return m, text
def decode_data(hash, enc):
    """The inverse of `encode_data`."""
    text = urllib.unquote(enc)
    m = hashlib.md5(settings.SECRET_KEY + text).hexdigest()[:12]
    if m != hash:
        raise Exception("Bad hash!")
    data = pickle.loads(zlib.decompress(text.decode('base64')))
    return data

def handler404(request):
    return render(request, '404.html', status=404)

def basic_context(request):
    staff_reg_url = None
    if request.user.is_superuser:
        expires = (timezone.now()+timedelta(days=1)).strftime('%x%X')
        staff_reg_url = reverse('website:register',args=[''.join(encode_data(expires))])
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
    return {'iquise':iquise,'useAnalytics': useAnalytics,'notifications':notifications,'donors':donors,'staff_reg_url':staff_reg_url}

def index(request):
    presentations = []
    today = timezone.now()
    session = Session.acvite_session()
    notification = None
    if session: # Current session is the one that hasn't ended and has the earliest start date
        events = session.event_set.filter(date__gte=timezone.now()).order_by('date')
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
    template_name = 'forms/base.html'
    form_class = PersonForm
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super(join, self).get_context_data(**kwargs)
        context['form_title'] = 'Join our iQuISE Community'
        context['tab_title'] = 'Join'
        context.update(basic_context(self.request))
        return context

    def form_valid(self,form):
        form.join_method = Person.WEBSITE
        form.save()
        return super(join, self).form_valid(form)

def staff_register(request, hash):
    context = basic_context(request)
    # Authenticate
    try:
        expires = timezone.datetime.strptime(decode_data(hash[:12],hash[12:]),'%x%X')
    except:
        context['form_title'] = 'Staff Registration Form: Contact superuser'
        context['tab_title'] = 'Staff Registration'
        context['notifications'].append('Bad URL')
        return render(request, 'forms/base.html', context)
    expires = pytz.utc.localize(expires)
    if timezone.now() > expires:
        context['form_title'] = 'Staff Registration Form: Contact superuser'
        context['tab_title'] = 'Staff Registration'
        context['notifications'].append('Expired URL')
        return render(request, 'forms/base.html', context)
    # Main
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save() # Need actual save to get id value
            user.groups.add(Group.objects.get(name='leadership'))
            user.is_staff = True
            user.save() # Resave now that updated (should signal profile save)
            return HttpResponseRedirect(reverse('admin:auth_user_change',args=[user.id]))

    else:
        form = RegistrationForm()
    
    context['form_title'] = 'Staff Registration Form'
    context['tab_title'] = 'Staff Registration'
    context['form'] = form
    return render(request, 'forms/base.html', context)