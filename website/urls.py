from django.urls import re_path

from . import views

app_name = 'website'
urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^presentation/(?P<presentation_id>[0-9]+)/$', views.presentation, name='presentation'),
    re_path(r'^archive/$',views.archive, name='archive'),
    re_path(r'^scheduler/$', views.scheduler, name='scheduler'),
]
