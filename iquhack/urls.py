from django.conf.urls import url

from . import views

ISO_REGEX = r"[0-9]{4}-[0-9]{0,2}-[0-9]{0,2}"

app_name = 'iquhack'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^profile/$', views.profile_view, name='profile'),
    url('^(?P<start_date>%s)$' % ISO_REGEX, views.index, name='hackathon'),
    url('^(?P<start_date>%s)/apply/$' % ISO_REGEX,views.AppView.as_view(), name='app'),
    url('^(?P<start_date>%s)/manage/$' % ISO_REGEX,views.manage_view, name='manage'),
    url('^(?P<start_date>%s)/applications/download/$' % ISO_REGEX,views.all_apps_download, name='download_apps'),
]
