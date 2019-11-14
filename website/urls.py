from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

app_name = 'website'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^presentation/(?P<presentation_id>[0-9]+)/$', views.presentation, name='presentation'),
    url(r'^leadership/$', views.people, name='people'),
    url(r'^join/$',views.join.as_view(), name='join'),
    url(r'^archive/$',views.archive, name='archive'),
    url(r'^register/(?P<hash>.*)/$', views.staff_register, name="register"),
    url(r'^scheduler/$', views.scheduler, name='scheduler'),
    url(r'^(?i)iQuHACK/$', TemplateView.as_view(template_name='iquhack.html'), name='iquhack'),
]
