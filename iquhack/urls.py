from django.conf.urls import url

from . import views

ISO_REGEX = r"[0-9]{4}-[0-9]{0,2}-[0-9]{0,2}"

app_name = 'iquhack'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url('^(?P<start_date>%s)$' % ISO_REGEX, views.index, name='hackathon'),
]
