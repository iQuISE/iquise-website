from django.urls import re_path

from . import views

app_name = 'members'
urlpatterns = [
    re_path(r'^leadership/$', views.committee, name='people_deprecated'), # deprecated, but don't delete so existing hyperlinks stil work
    re_path(r'^exec/$', views.committee, name='people'),
    re_path(r'^join/$', views.Join.as_view(), name='join'),
    re_path(r'^staff/(?P<user>.*)/$', views.staff_member, name="staff"),
    re_path(r'^committee/(?P<name>.*)/$', views.committee, name="committee"),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
        views.confirm_email, name='confirm_email'),
    re_path(r'^profile/$',views.profile_view, name='profile'),
]
