# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import Presentation
from .models import Person

admin.site.register(Presentation)
admin.site.register(Person)