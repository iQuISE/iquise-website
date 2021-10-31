"""iquise URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from members.forms import LoginForm

admin.site.site_header = 'iQuISE Administration'

handler400 = 'website.views.handler404'
handler404 = 'website.views.handler404'

urlpatterns = [
    url(
        r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('website/favicon.ico'),
            permanent=False),
        name="favicon"
    ),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login', views.LoginView.as_view(authentication_form=LoginForm), name='login'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^(?i)iQuHACK/', include('iquhack.urls')),
    url(r'^election/', include('elections.urls')),
    url(r'^', include('website.urls')),
    url(r'^', include('members.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
