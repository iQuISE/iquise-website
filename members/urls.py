from django.conf.urls import url

from . import views
from django.contrib.auth.models import Group

app_name = 'members'
urlpatterns = [
    url(r'^leadership/$', views.committee, name='people_deprecated'), # deprecated, but don't delete so existing hyperlinks stil work
    url(r'^exec/$', views.committee, name='people'),
    url(r'^join/$',views.Join.as_view(), name='join'),
    url(r'^register/(?P<hash_>.*)/$', views.staff_register, name="register"),
    url(r'^staff/(?P<user>.*)/$', views.staff_member, name="staff"),
    url(r'^committee/(?P<name>.*)/$', views.committee, name="committee")
]
