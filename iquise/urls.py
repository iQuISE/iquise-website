"""iquise URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
"""
from django.urls import include, re_path, path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from members.forms import LoginForm

from .overrides import PasswordResetConfirmView, PasswordResetForm

admin.site.site_header = 'iQuISE Administration'

handler400 = 'website.views.handler404'
handler404 = 'website.views.handler404'

urlpatterns = [
    re_path(
        r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('website/favicon.ico'),
            permanent=False),
        name="favicon"
    ),
    path('admin/', admin.site.urls),
    re_path(r'^accounts/login', views.LoginView.as_view(authentication_form=LoginForm), name='login'),
    re_path(r'^accounts/password_reset/$',
        views.PasswordResetView.as_view(form_class=PasswordResetForm),
        name='password_reset'
    ),
    re_path(r'^accounts/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/', include('django.contrib.auth.urls')),
    re_path(r'^[iI][qQ][uU][hH][aA][cC][kK]/', include('iquhack.urls')),
    re_path(r'^election/', include('elections.urls')),
    path('', include('website.urls')),
    path('', include('members.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
