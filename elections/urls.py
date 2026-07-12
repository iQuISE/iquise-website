from django.urls import re_path

from . import views

app_name = 'elections'
urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^vote/$', views.vote, name='vote'),
    re_path(r'^nominate/$', views.nominate, name='nominate'),
]
