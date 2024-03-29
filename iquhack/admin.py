# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from django.contrib import admin
from django.urls import reverse
from django.shortcuts import redirect
from django.db import transaction
from django.utils.safestring import mark_safe


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
    Guardian,
    Profile,
    Address,
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

def accept(modeladmin, request, queryset):
    with transaction.atomic():
        for app in queryset:
            app.accept()
    return redirect(reverse("admin:iquhack_application_changelist"))
accept.short_description = "Accept selected applications"

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("__unicode__", "hackathon")
    list_filter = ("hackathon", "accepted")
    readonly_fields = ("user", "hackathon", "accepted")
    search_fields = ("user__email", "user__first_name", "user__last_name", "responses")
    actions = (accept, )

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            help_texts = {
                "user": mark_safe("<a href=%s>Go to user profile</a>"%reverse("admin:auth_user_change", args=[obj.user.id])),
                "hackathon": mark_safe("<a href=%s>Go to hackathon</a>"%reverse("admin:iquhack_hackathon_change", args=[obj.hackathon.id])),
            }
            kwargs.update({"help_texts": help_texts})
        return super(ApplicationAdmin, self).get_form(request, obj, **kwargs)

class GuardianInline(admin.TabularInline):
    model = Guardian
    extra = 1

class ProfileAdmin(admin.ModelAdmin):
    search_fields = ("user__email", "user__first_name", "user__last_name")
    inlines = (GuardianInline, )

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            help_texts = {
                "user": mark_safe("<a href=%s>Go to user profile</a>"%reverse("admin:auth_user_change", args=[obj.user.id])),
            }
            kwargs.update({"help_texts": help_texts})
        return super(ProfileAdmin, self).get_form(request, obj, **kwargs)


admin.site.register(Hackathon, HackathonAdmin)
admin.site.register(Sponsor)
admin.site.register(Tier)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(SectionTemplate)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Guardian)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Address)