from django.urls import re_path

from . import views

ISO_REGEX = r"[0-9]{4}-[0-9]{0,2}-[0-9]{0,2}"

app_name = 'iquhack'
urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^profile/$', views.profile_view, name='profile'),
    re_path('^(?P<start_date>%s)$' % ISO_REGEX, views.index, name='hackathon'),
    re_path('^(?P<start_date>%s)/apply/$' % ISO_REGEX,views.AppView.as_view(), name='app'),
    re_path('^(?P<start_date>%s)/manage/$' % ISO_REGEX,views.manage_view, name='manage'),
    re_path('^(?P<start_date>%s)/applications/download/$' % ISO_REGEX,views.all_apps_download, name='download_apps'),
    re_path('^(?P<start_date>%s)/participants/download/$' % ISO_REGEX,views.all_partipants_download, name='download_partipants'),
]
