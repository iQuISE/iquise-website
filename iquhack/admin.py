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
            "fields": ("start_date", "end_date", "back_drop_image", "published")
        }),
        ("Sponsor Logos", {
            "description": "Platform sponsors will use these directly. Sponsor Tiers will compute their absolute value relative to these.",
            "fields": ("logo_max_height", "logo_max_side_margin", "logo_max_bottom_margin")
        }),
        ("Registration", {
            "fields": ("link", "opens", "deadline", "early_note", "open_note", "closed_note")
        }),
    )
    inlines = (SponsorInline, )

class SponsorAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "hackathon", "tier", "platform", "have_logo", "have_agreement")
    list_filter = ("hackathon", )

admin.site.register(Hackathon, HackathonAdmin)
admin.site.register(Sponsor, SponsorAdmin)
admin.site.register(Tier)
