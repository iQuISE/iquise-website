# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Hackathon, Sponsor, Tier, Sponsorship

class SponsorshipInline(admin.TabularInline):
    model = Sponsorship
    extra = 1

class SponsorshipInline_ReadOnly(admin.TabularInline):
    model = Sponsorship
    extra = 0
    readonly_fields = ("hackathon", "sponsor", "tier", "platform", "agreement")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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
    inlines = (SponsorshipInline, )

class SponsorAdmin(admin.ModelAdmin):
    inlines = (SponsorshipInline_ReadOnly, )

admin.site.register(Hackathon, HackathonAdmin)
admin.site.register(Sponsor, SponsorAdmin)
admin.site.register(Tier)
