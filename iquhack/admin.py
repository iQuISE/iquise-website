# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import (
    Hackathon,
    Sponsor,
    Tier,
    Sponsorship,
    Section,
    UsedSection,
    FAQ,
    UsedFAQ,
)

class SponsorshipInline(admin.TabularInline):
    model = Sponsorship
    extra = 1

class SectionInline(admin.TabularInline):
    model = UsedSection
    verbose_name_plural = "Sections"
    extra = 1

class FAQInline(admin.TabularInline):
    model = UsedFAQ
    verbose_name_plural = "FAQs"
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
    inlines = (SponsorshipInline, FAQInline, SectionInline)

class GeneralContentAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "general")

admin.site.register(Hackathon, HackathonAdmin)
admin.site.register(Sponsor)
admin.site.register(Tier)
admin.site.register(FAQ, GeneralContentAdmin)
admin.site.register(Section, GeneralContentAdmin)