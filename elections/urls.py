from django.conf.urls import url

from . import views

app_name = 'elections'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^vote/$', views.vote, name='vote'),
    url(r'^nominate/$', views.nominate, name='nominate'),
]
