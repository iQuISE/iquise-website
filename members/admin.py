# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User, Group
from django.contrib.admin import SimpleListFilter

from website.admin import redirectFromAdmin
from .models import *

# TODO: Generalize make_subscribed. Ref:
# https://stackoverflow.com/questions/11764709/can-you-add-parameters-to-django-custom-admin-actions
def make_subscribed(modeladmin, request, queryset):
    email_list = EmailList.objects.get(address="iquise-associates@mit.edu")
    for user in queryset:
        user.profile.subscriptions.add(email_list)
    return redirect(reverse('admin:auth_user_changelist'))
make_subscribed.short_description = 'Mark selected people subscribed'


class PositionAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
        """Hide this model"""
        return {}

admin.site.register(EmailList)
admin.site.register(School)
admin.site.register(Position, PositionAdmin)
admin.site.register(Term)

# Update User admin to include profile inline
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class PositionsHeldFormSet(BaseInlineFormSet):
    def clean(self):
        # If there are errors, issue a "warning" of a common validation error caused
        # by processing formset in a certain order.
        if any(self.errors):
            seen = set()
            duplicates = set()
            for posheld in self.extra_forms + self.forms:
                pos = posheld.cleaned_data.get("position")
                if not pos: continue
                if pos not in seen:
                    seen.add(pos)
                else:
                    duplicates.add(pos)
            if duplicates:
                plural = "s" if len(duplicates) > 1 else ""
                msg = (
                    "It appears you tried to create and/or edit the same type of position%s (%s). "
                    "While not necessarily the error, it is a likely candidate. "
                    "It is recommended you perform such operations one at a time."
                ) % (plural, ", ".join(map(str, duplicates)))
                raise ValidationError(msg)

class PositionHeldInline(admin.TabularInline):
    model = PositionHeld
    formset = PositionsHeldFormSet
    fields = ("user", "position", "start", "stop")
    extra = 0

class PositionsInline(admin.TabularInline):
    model = Position
    extra = 0

    def get_queryset(self, request):
        qs = super(PositionsInline, self).get_queryset(request)
        return Position.exclude_default(qs)

class MyUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(MyUserChangeForm, self).__init__(*args, **kwargs)
        # make user email field required
        if 'first_name' in self.fields:
            self.fields['first_name'].required = True
        if 'last_name' in self.fields:
            self.fields['last_name'].required = True
        if 'email' in self.fields:
            self.fields['email'].required = True

class EmailFilter(SimpleListFilter):
    title = 'MIT'
    parameter_name = 'MIT'

    def lookups(self, request, model_admin):
        return [("mit.edu", "MIT"), ("harvard.edu", "Harvard"), ("", "Neither")]

    def queryset(self, request, queryset):
        val = self.value()
        if val is not None:
            if val == "":
                return queryset.filter(email=val)
            return queryset.filter(email__iendswith=val)
        return queryset

class SubscriptionFilter(SimpleListFilter):
    title = 'subscription'
    parameter_name = 'subscription'
    filter_type = "filter"

    def lookups(self, request, model_admin):
        return [(e, e) for e in EmailList.objects.all()]

    def queryset(self, request, queryset):
        val = self.value()
        if val:
            operation = getattr(queryset, self.filter_type)
            return operation(profile__subscriptions=EmailList.objects.get(address=val))
        return queryset

class NotSubscribedFilter(SubscriptionFilter):
    title = "no subscription"
    parameter_name = "no subscription"
    filter_type = "exclude"

class CustomUserAdmin(UserAdmin):
    form = MyUserChangeForm
    add_form = UserCreationForm
    staff_fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
    )
    list_filter = ("is_active", "is_staff", EmailFilter, NotSubscribedFilter, SubscriptionFilter)
    inlines = (ProfileInline, PositionHeldInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_select_related = ('profile',) # Streamline database queries
    actions = (make_subscribed,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

    def change_view(self, request, id, *args, **kwargs):
        # for non-superuser [NOTE this does not provide security, just nicer view]
        if not request.user.is_superuser:
            try:
                self.fieldsets = (None, {'fields': ()}),
                try:
                    if request.user == User.objects.get(id=id):
                        self.fieldsets = self.staff_fieldsets
                except User.DoesNotExist:
                    pass
                response = super(CustomUserAdmin, self).change_view(request, id, *args, **kwargs)
            finally:
                # Reset fieldsets to its original value
                self.fieldsets = UserAdmin.fieldsets
            return response
        else:
            return super(CustomUserAdmin, self).change_view(request, id, *args, **kwargs)

    def get_queryset(self, request):
        qs = super(CustomUserAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(is_superuser=False)
        return qs

class CommitteeFormSet(BaseInlineFormSet):
    def save(self, commit=True):
        saved_instances = super(CommitteeFormSet, self).save(commit)
        if commit and not saved_instances: # Create even if user didn't specify parent
            saved_instances.append(Committee.objects.get_or_create(group=self.instance))
        return saved_instances

class CommitteeInline(admin.StackedInline):
    # TODO: Would be nice to edit membership/positions from here
    model = Committee
    formset = CommitteeFormSet
    can_delete = False
    verbose_name_plural = 'Committee Info'
    fk_name = 'group'

class CustomGroupAdmin(GroupAdmin):
    inlines = (CommitteeInline, PositionsInline, )
    list_display = ("__unicode__", "show_email", "email", "email_inherited")

    def show_email(self, obj):
        return obj.committee.show_email
    show_email.boolean = True

    def email(self, obj):
        return obj.committee.email
    
    def email_inherited(self, obj):
        return obj.committee.contact_email != obj.committee.email
    email_inherited.boolean = True

    def has_description(self, obj):
        return obj.committee.description != ""
    has_description.boolean = True

# Reset admin User/Group
admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, CustomGroupAdmin)
