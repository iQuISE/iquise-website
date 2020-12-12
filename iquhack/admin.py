# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Hackathon, Sponsor, Tier, CompanyContact

admin.site.register(Hackathon)
admin.site.register(Sponsor)
admin.site.register(Tier)
admin.site.register(CompanyContact)