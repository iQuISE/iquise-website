# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

from website.forms import PresentationForm
from website.models import *

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
        ret_url = request.GET.get('next',None)
        if ret_url:
            return redirect(ret_url)
        return super(redirectFromAdmin, self).response_add(request, obj)
    def response_change(self, request, obj):
        ret_url = request.GET.get('next',None)
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
    verbose_name = 'Event (Timezone: %s)'%settings.TIME_ZONE
    verbose_name_plural = 'Event (Timezone: %s)'%settings.TIME_ZONE

class SessionAdmin(admin.ModelAdmin):
    readonly_fields = ('slug',)
    inlines = (EventInline, )
    list_display = ('__unicode__','start','stop')
    def get_form(self, request, obj=None, **kwargs):
        form = super(SessionAdmin, self).get_form(request, obj, **kwargs)
        form.Media = ExtraMedia # Change Edit -> Details link text
        return form

class PresentationInLine(admin.TabularInline):
    #fields = ('presentation__primary_contact','presentation__presenters','presentation__title','presentation__theme','presentation__confirmed')
    model = Presentation.event.through
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
    readonly_fields = ('profile_image_thumb',)
    list_display = ('__unicode__', 'affiliation')

class EmbeddedVideoAdmin(admin.ModelAdmin):
    fields = ('engine', 'video_id', 'public')
    list_display = ('__unicode__', 'engine_name','public')

    def engine_name(self,obj):
        return obj.engine.name


class PresentationAdmin(redirectFromAdmin):
    # Hide it (but we need the URLs for it)
    form = PresentationForm
    get_model_perms = lambda self, req: {}
    list_display = ('__unicode__', 'get_session','get_presenters')
    def get_session(self,obj):
        session = 'None'
        event = obj.event.first()
        if event:
            session = unicode(event.session)
        return u'%s'%session
    def get_form(self, request, obj=None, **kwargs):
        form = super(PresentationAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['primary_contact'].initial = request.user
        session = request.GET.get('session',None)
        if session:
            try:
                form.base_fields['event'].queryset = Session.objects.get(slug=session).event_set.all()
            except Session.DoesNotExist:
                form.base_fields['event'].queryset = Session.active_session().event_set.all()
                form.base_fields['event'].help_text = 'Session in URL does not exist; assuming active session. If not, you can set via Session -> Event -> details'
        else: # Default active
            form.base_fields['event'].queryset = Session.active_session().event_set.all()
            form.base_fields['event'].help_text = 'No session specified in URL, assuming active session. If not, you can set via Session -> Event -> details'
        return form

class TemporaryTokenAdmin(admin.ModelAdmin):
    list_display = ("__str__", "valid_through", "times_used", "is_valid")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")
    readonly_fields = ("token", "times_used")

admin.site.register(Donor,DonorAdmin)
admin.site.register(IQUISE,IQUISEAdmin)
admin.site.register(Session,SessionAdmin)
admin.site.register(Event,EventAdmin)
admin.site.register(Presenter,PresenterAdmin)
admin.site.register(Presentation,PresentationAdmin)
admin.site.register(EmbeddedVideo,EmbeddedVideoAdmin)
admin.site.register(EmbedEngine)
admin.site.register(TemporaryToken, TemporaryTokenAdmin)