# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.conf import settings
from django.contrib import admin

from .models import *
# Register your models here.

class redirectFromAdmin(admin.ModelAdmin):
    # Redirect from where you came from if possible
    def response_add(self, request, obj):
        ret_url = request.GET.get('last',None)
        if ret_url:
            return redirect(ret_url)
        return super(redirectFromAdmin, self).response_add(request, obj)
    def response_change(self, request, obj):
        ret_url = request.GET.get('last',None)
        if ret_url:
            return redirect(ret_url)
        return super(redirectFromAdmin, self).response_change(request, obj)

class MeetingAdmin(redirectFromAdmin):
    list_display = ('__str__','date')

    def get_form(self, request, obj=None, **kwargs):
        form = super(MeetingAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['attendees'].initial = [request.user]
        return form

admin.site.register(Meeting,MeetingAdmin)
