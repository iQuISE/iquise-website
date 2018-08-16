# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# Register your models here.
from .models import *

class IQUISEAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # if there's already an entry, do not allow adding
        count = IQUISE.objects.all().count()
        if count == 0:
            return True and request.user.has_perm('website.add_iquise')

        return False

class PersonAdmin(admin.ModelAdmin):
    readonly_fields = ['join_method','record_created','last_modified']

class PresentationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'date','presenter')

# Update admin to include profile inline
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
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

admin.site.register(Presentation,PresentationAdmin)
admin.site.register(Person,PersonAdmin)
admin.site.register(Department)
admin.site.register(School)
admin.site.register(IQUISE,IQUISEAdmin)
# Reset auth User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
