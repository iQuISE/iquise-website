# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import *

class IQUISEAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # if there's already an entry, do not allow adding
        count = IQUISE.objects.all().count()
        if count == 0:
            return True and request.user.has_perm('website.add_iquise')

        return False

admin.site.register(Presentation)
admin.site.register(Person)
admin.site.register(IQUISE,IQUISEAdmin)
