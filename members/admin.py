# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User

from website.admin import redirectFromAdmin
from .models import *

def make_subscribed(modeladmin, request, queryset):
    queryset.update(subscribed=True)
    return redirect(reverse('admin:website_person_changelist'))
make_subscribed.short_description = 'Mark selected people subscribed'

class PersonAdmin(redirectFromAdmin):
    readonly_fields = ('join_method',)
    list_display = ('__unicode__', 'subscribed','lab','email','year','join_method')
    list_filter = ('subscribed','year','join_method',)
    actions = (make_subscribed,)

# Update User admin to include profile inline
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class EmailRequiredMixin(object):
    def __init__(self, *args, **kwargs):
        super(EmailRequiredMixin, self).__init__(*args, **kwargs)
        # make user email field required
        if 'first_name' in self.fields:
            self.fields['first_name'].required = True
        if 'last_name' in self.fields:
            self.fields['last_name'].required = True
        if 'email' in self.fields:
            self.fields['email'].required = True
class MyUserCreationForm(UserCreationForm):
    pass
class MyUserChangeForm(EmailRequiredMixin, UserChangeForm):
    pass
class CustomUserAdmin(UserAdmin):
    form = MyUserChangeForm
    add_form = MyUserCreationForm
    staff_fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
    )
    list_filter = () # Small group, not necessary
    inlines = (ProfileInline, )
    list_display = ('username','get_role', 'email', 'first_name', 'last_name', 'is_staff')
    list_select_related = ('profile', ) # Streamline database queries

    def get_role(self,instance):
        return instance.profile.role
    get_role.short_description = 'Role'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

    def change_view(self, request, id, *args, **kwargs):
        # for non-superuser [NOTE this does not provide security, just niceer view]
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

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        obj.save()

admin.site.register(Person,PersonAdmin)
admin.site.register(Department)
admin.site.register(School)
# Reset admin User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
