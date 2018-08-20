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
        form.base_fields['modified_by'].initial = request.user
        if obj:
            with open(obj.minutes_path,'r') as fid:
                print dir(form.base_fields['minutes_path'])
                form.base_fields['minutes_path'].value = fid.read()
        return form

    def save_model(self, request, obj, form, change):
        # replace minutes with file path
        path = os.path.join(settings.BASE_DIR,'minutes')
        fname = os.path.join(path,str(obj.date)+'.txt')
        if not os.path.isdir(path):
            os.mkdir(path)
        with open(fname,'w') as fid:
            fid.write(obj.minutes_path)
        obj.minutes_path = fname
        super(MeetingAdmin,self).save_model(request, obj, form, change)

admin.site.register(Meeting,MeetingAdmin)