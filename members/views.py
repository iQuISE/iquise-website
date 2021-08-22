# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytz
import datetime
import traceback

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, Http404, redirect
from django.utils import timezone
from django.urls import reverse
from django.template import loader
from django.conf import settings
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User, Group
from django.views.generic.edit import FormView
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text

from iquise.utils import basic_context, decode_data, send_mail

from members.forms import JoinForm, RegistrationForm
from members.models import Profile, Term, get_term_containing
from members.tokens import email_confirmation_token

class Join(FormView):
    template_name = 'members/join_community.html'
    form_class = JoinForm
    success_url = '/'

    def get_form_kwargs(self):
        kwargs = super(Join, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(Join, self).get_context_data(**kwargs)
        context['form_title'] = 'Join our Community'
        context['tab_title'] = 'Join'
        context.update(basic_context(self.request))
        return context

    def form_valid(self, form):
        new_user = form.save()
        notification = "Submission received! Check your email to confirm your email address."
        self.request.session["extra_notification"] = notification
        uid = urlsafe_base64_encode(force_bytes(new_user.pk))
        token = email_confirmation_token.make_token(new_user)
        confirm_link = self.request.build_absolute_uri(
            reverse('members:confirm_email', kwargs={"uidb64": uid, "token": token})
        )
        msg = (
            "Thank you for making an account with iQuISE! "
            "We need to confirm your email address. "
            "If you did not register, you can ignore this email.\n\n"
            "Otherwise click this link below to confirm your email:\n%s"
        ) % confirm_link
        send_mail("[iQuISE] Validate Email Address", msg, recipient_list=[new_user.email])
        return super(Join, self).form_valid(form)

def confirm_email(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and email_confirmation_token.check_token(user, token):
        user.profile.email_confirmed = True
        user.profile.save()
        request.session["extra_notification"] = "Email confirmed!"
    else:
        request.session["extra_notification"] = "Activation link is invalid."
    return redirect("website:index")

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

def committee(request, name=None):
    multiple_groups = False
    if name:
        group = get_object_or_404(Group, name__iexact=name)
    else:
        group = Group.objects.filter(committee__parent__isnull=True)
        n_group = group.count()
        if n_group == 0:
            raise Http404()
        elif n_group > 1:
            multiple_groups = True
        group = group.first()
    # TODO: send full list and make date next/back entirely frontend JS
    date_str = request.GET.get("date")
    date = timezone.now().date()
    notifications = []
    if date_str:
        try:
            date_els = [int(item) for item in date_str.split("-")] # Convert to list of ints: [2020, 12, 12]
            date = datetime.date(*date_els)
        except:
            if settings.DEBUG:
                notifications = [mark_safe(traceback.format_exc().replace("\n", "<br>"))]
            else: # Don't include any details of backend!
                notifications = ["Failed to decode '%s', should be 'YYYY-MM-DD'" % date_str]
    term = get_term_containing(date)
    # Need new query to get surrounding ones (not include equality in comparison should be sufficient)
    if term: # Remember sorted by newest to oldest
        next_term = Term.objects.filter(start__gt=term.start).last()
        previous_term = Term.objects.filter(start__lt=term.start).first()
    else: # Could still be a future term
        next_term = Term.objects.filter(start__gte=date).last()
        previous_term = None

    pos_held = group.committee.get_positions_held(term).order_by("position")
    if term:
        start = term.start
        stop = term.get_end()
    else:
        if pos_held: # Better to not call .exists() since we iterate later anyway (django caches)
            start = pos_held.first().start
        else:
            start = date
        if next_term:
            stop = next_term.start
        elif pos_held:
            stop = pos_held.last().start
        else:
            stop = None
    context = {
        'group': group,
        'pos_held': pos_held,
        'start': start,
        'stop': stop,
        'next_term': next_term,
        'previous_term': previous_term,
        'multiple_groups': multiple_groups,
    }
    context.update(basic_context(request))
    context["notifications"] = context.get("notifications", []) + notifications
    return render(request, "members/committee.html", context)
