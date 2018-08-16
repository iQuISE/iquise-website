# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.shortcuts import redirect

# Register your models here.
from .models import *

class redirectFromAdmin(admin.ModelAdmin):
    # Redirect from where you came from if possible
    def response_add(self, request, obj):
        ret_url = request.GET.get('return',None)
        if ret_url:
            return redirect(ret_url)
        return super(redirectFromAdmin, self).response_add(request, obj)
    def response_change(self, request, obj):
        ret_url = request.GET.get('return',None)
        if ret_url:
            return redirect(ret_url)
        return super(redirectFromAdmin, self).response_change(request, obj)

class IQUISEAdmin(redirectFromAdmin):
    def has_add_permission(self, request):
        # if there's already an entry, do not allow adding
        count = IQUISE.objects.all().count()
        if count == 0:
            return True and request.user.has_perm('website.add_iquise')

        return False

class PersonAdmin(admin.ModelAdmin):
    readonly_fields = ['join_method','record_created','last_modified']

class PresentationAdmin(redirectFromAdmin):
    list_display = ('__str__', 'date','presenter')

# Update admin to include profile inline
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class EmailRequiredMixin(object):
    def __init__(self, *args, **kwargs):
        super(EmailRequiredMixin, self).__init__(*args, **kwargs)
        # make user email field required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
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

    def change_view(self, request, *args, **kwargs):
        # for non-superuser
        if not request.user.is_superuser:
            try:
                self.fieldsets = self.staff_fieldsets
                response = super(CustomUserAdmin, self).change_view(request, *args, **kwargs)
            finally:
                # Reset fieldsets to its original value
                self.fieldsets = UserAdmin.fieldsets
            return response
        else:
            return super(CustomUserAdmin, self).change_view(request, *args, **kwargs)

    def get_queryset(self, request):
        qs = super(UserAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(is_superuser=False)
        return qs

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        obj.save()

admin.site.register(Presentation,PresentationAdmin)
admin.site.register(Person,PersonAdmin)
admin.site.register(Department)
admin.site.register(School)
admin.site.register(IQUISE,IQUISEAdmin)
# Reset auth User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
