# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import (
    Hackathon,
    Sponsor,
    Tier,
    Sponsorship,
    Section,
    SectionTemplate,
    Attachment,
    FAQ,
    UsedFAQ,
    Application,
)

class SponsorshipInline(admin.TabularInline):
    model = Sponsorship
    extra = 1

class SectionInline(admin.TabularInline):
    model = Section
    verbose_name_plural = "Sections (Follow change link to edit attachments)"
    extra = 1
    show_change_link = True

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 1

class FAQInline(admin.TabularInline):
    model = UsedFAQ
    verbose_name_plural = "FAQs"
    extra = 1

class HackathonAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "end_date", "published", "open")
    fieldsets = (
        (None, {
            "fields": ("start_date", "end_date", "back_drop_image", "organizing_committee", "published")
        }),
        ("Sponsor Logos", {
            "description": "Platform sponsors will use these directly. Sponsor Tiers will compute their absolute value relative to these.",
            "fields": ("logo_max_height", "logo_max_side_margin", "logo_max_bottom_margin")
        }),
        ("Registration", {
            "fields": ("app_questions", "opens", "deadline", "early_note", "open_note", "closed_note")
        }),
    )
    inlines = (SponsorshipInline, FAQInline, SectionInline)

class SectionAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "hackathon")
    list_filter = ("hackathon",)
    inlines = (AttachmentInline,)

class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "section")
    list_filter = ("section",)

class FAQAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "general")
    list_filter = ("general", )


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "hackathon")
    list_filter = ("hackathon", )
    readonly_fields = ("user", "hackathon", "responses")

admin.site.register(Hackathon, HackathonAdmin)
admin.site.register(Sponsor)
admin.site.register(Tier)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(SectionTemplate)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(Application, ApplicationAdmin)