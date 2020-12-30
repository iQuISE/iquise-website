# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytz

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.template import loader
from django.contrib.auth.models import User, Group
from django.views.generic.edit import FormView

from members.forms import PersonForm, RegistrationForm
from members.models import Person
from iquise.utils import basic_context, decode_data



class join(FormView):
    template_name = 'forms/base.html'
    form_class = PersonForm
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super(join, self).get_context_data(**kwargs)
        context['form_title'] = 'Join our Community'
        context['tab_title'] = 'Join'
        context.update(basic_context(self.request))
        return context

    def form_valid(self,form):
        form.join_method = Person.WEBSITE
        form.save()
        return super(join, self).form_valid(form)

def people(request):
    people = User.objects.all().filter(is_superuser=False).filter(is_active=True) # Filter "iquise"
    context = {
        'people': people,
    }
    context.update(basic_context(request))
    return render(request,'members/exec.html',context)

def staff_member(request, user):
    staff = get_object_or_404(User, username=user)
    context = {
        'staff': staff,
    }
    context.update(basic_context(request))
    return render(request, "members/staff_member.html", context)

def staff_register(request, hash_):
    context = basic_context(request)
    # Authenticate
    try:
        expires = timezone.datetime.strptime(decode_data(hash_[:12],hash_[12:]),'%x%X')
    except:
        context['form_title'] = 'Staff Registration Form: Contact superuser'
        context['tab_title'] = 'Staff Registration'
        context['notifications'].append('Bad URL')
        return render(request, 'forms/base.html', context)
    expires = pytz.utc.localize(expires)
    if timezone.localtime() > expires:
        context['form_title'] = 'Staff Registration Form: Contact superuser'
        context['tab_title'] = 'Staff Registration'
        context['notifications'].append('Expired URL')
        return render(request, 'forms/base.html', context)
    # Main
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save() # Need actual save to get id value
            user.groups.add(Group.objects.get(name='exec'))
            user.is_staff = True
            user.save() # Resave now that updated (should signal profile save)
            return HttpResponseRedirect(reverse('admin:auth_user_change',args=[user.id])+'?last=/')

    else:
        form = RegistrationForm()

    context['form_title'] = 'Staff Registration Form'
    context['tab_title'] = 'Staff Registration'
    context['form'] = form
    return render(request, 'forms/base.html', context)