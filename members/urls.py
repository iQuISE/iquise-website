from django.conf.urls import url

from . import views

app_name = 'members'
urlpatterns = [
    url(r'^leadership/$', views.people, name='people_deprecated'), # deprecated, but don't delete so existing hyperlinks stil work
    url(r'^exec/$', views.people, name='people'),
    url(r'^join/$',views.join.as_view(), name='join'),
    url(r'^register/(?P<hash>.*)/$', views.staff_register, name="register"),
    url(r'^exec/(?P<user>.*)/$', views.staff_member, name="staff")
]
