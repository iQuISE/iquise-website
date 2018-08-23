# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.urls import reverse

# Register your models here.
from .models import *

class ExtraMedia:
    # Use in form if needed
    js = (
        'website/assets/js/jquery.min.js', # jquery
        'website/assets/js/custom.js',     # custom
    )

class hideInlinePopup(admin.ModelAdmin):
    def change_view(self, request, id, *args, **kwargs):
        # If this is a popup, hide the inlines
        if int(request.GET.get('_popup','0')):
            try:
                self.inlines = ()
                response = super(hideInlinePopup, self).change_view(request, id, *args, **kwargs)
            finally:
                # Reset fieldsets to its original value
                self.inlines = type(self).inlines
            return response
        else:
            return super(hideInlinePopup, self).change_view(request, id, *args, **kwargs)

class redirectFromAdmin(admin.ModelAdmin):
    # Redirect from where you came from if possible
    def response_add(self, request, obj):
        ret_url = request.GET.get('last',None)
        if ret_url:
            return redirect(ret_url)
        return super(redirectFromAdmin, self).response_add(request, obj)
    def response_change(self, request, obj):
        ret_url = request.GET.get('last',None)
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

class DonationInline(admin.TabularInline):
    model = Donation
    fk_name = 'donor'
    extra = 0

class DonorAdmin(redirectFromAdmin):
    inlines = (DonationInline,)

class EventInline(admin.TabularInline):
    exclude = ('audience',)
    model = Event
    fk_name = 'session'
    extra = 0
    show_change_link = True

class SessionAdmin(admin.ModelAdmin):
    readonly_fields = ('slug',)
    inlines = (EventInline, )
    list_display = ('__str__','start','stop')
    def get_form(self, request, obj=None, **kwargs):
        form = super(SessionAdmin, self).get_form(request, obj, **kwargs)
        form.Media = ExtraMedia # Change Edit -> Details link text
        return form

class PresentationInLine(admin.TabularInline):
    fields = ('primary_contact','presenters','title','theme','confirmed')
    model = Presentation
    fk_name = 'event'
    extra = 0
    show_change_link = True

class EventAdmin(hideInlinePopup):
    # Hide it (but we need the URLs for it)
    get_model_perms = lambda self, req: {}
    inlines = (PresentationInLine, )
    def response_add(self, request, obj):
        if request.POST.get('_continue',None)==u'Save and continue editing' or int(request.GET.get('_popup','0')):
            return super(EventAdmin,self).response_add(request,obj)
        if obj:
            return redirect(reverse('admin:website_session_change',args=[obj.session.id]))
        return redirect(reverse('admin:website_session_changelist'))
    def response_change(self, request, obj):
        if request.POST.get('_continue',None)==u'Save and continue editing' or int(request.GET.get('_popup','0')):
            return super(EventAdmin,self).response_add(request,obj)
        if obj:
            return redirect(reverse('admin:website_session_change',args=[obj.session.id]))
        return redirect(reverse('admin:website_session_changelist'))
    def response_delete(self, request, obj_display, obj_id):
        if int(request.GET.get('_popup','0')):
            return super(EventAdmin,self).response_delete(request, obj_display, obj_id)
        id = int(obj_display[obj_display.index('[')+1:obj_display.index(']')])
        return redirect(reverse('admin:website_session_change',args=[id]))

class PresenterAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'affiliation')

class PresentationAdmin(redirectFromAdmin):
    # Hide it (but we need the URLs for it)
    get_model_perms = lambda self, req: {}
    list_display = ('__str__', 'event','get_presenters')
    def get_form(self, request, obj=None, **kwargs):
        form = super(PresentationAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['primary_contact'].initial = request.user
        session = request.GET.get('session',None)
        if session:
            try:
                form.base_fields['event'].queryset = Session.objects.get(slug=session).event_set.all()
            except Session.DoesNotExist:
                form.base_fields['event'].queryset = Session.acvite_session().event_set.all()
                form.base_fields['event'].help_text = 'Session in URL does not exist; assuming active session. If not, you can set via Session -> Event -> details'
        else: # Default active
            form.base_fields['event'].queryset = Session.acvite_session().event_set.all()
            form.base_fields['event'].help_text = 'No session specified in URL, assuming active session. If not, you can set via Session -> Event -> details'
        return form

class PersonAdmin(redirectFromAdmin):
    readonly_fields = ('join_method',)
    list_display = ('__str__', 'email','year','join_method')

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
        qs = super(UserAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(is_superuser=False)
        return qs

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        obj.save()

admin.site.register(Donor,DonorAdmin)
admin.site.register(IQUISE,IQUISEAdmin)
admin.site.register(Session,SessionAdmin)
admin.site.register(Event,EventAdmin)
admin.site.register(Presenter,PresenterAdmin)
admin.site.register(Presentation,PresentationAdmin)
admin.site.register(Person,PersonAdmin)
admin.site.register(Department)
admin.site.register(School)

# Reset admin User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
