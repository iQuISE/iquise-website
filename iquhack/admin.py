# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Hackathon, Sponsor, Tier

class SponsorInline(admin.TabularInline):
    model = Sponsor
    extra = 1

class HackathonAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "end_date", "published", "open")
    fieldsets = (
        (None, {
            "fields": ("start_date", "end_date", "back_drop_image", "published", "logo_max_height")
        }),
        ("Registration", {
            "fields": ("link", "opens", "deadline", "early_note", "open_note", "closed_note")
        }),
    )
    inlines = (SponsorInline, )

class SponsorAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "hackathon")

admin.site.register(Hackathon, HackathonAdmin)
admin.site.register(Sponsor, SponsorAdmin)
admin.site.register(Tier)