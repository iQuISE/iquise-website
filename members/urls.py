from django.conf.urls import url

from . import views

app_name = 'members'
urlpatterns = [
    url(r'^leadership/$', views.committee, name='people_deprecated'), # deprecated, but don't delete so existing hyperlinks stil work
    url(r'^exec/$', views.committee, name='people'),
    url(r'^join/$',views.Join.as_view(), name='join'),
    url(r'^staff/(?P<user>.*)/$', views.staff_member, name="staff"),
    url(r'^committee/(?P<name>.*)/$', views.committee, name="committee"),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.confirm_email, name='confirm_email'),
    url(r'^profile/$',views.ProfileView.as_view(), name='profile'),    
]
