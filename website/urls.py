from django.conf.urls import url

from . import views

app_name = 'website'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^presentation/(?P<presentation_id>[0-9]+)/$', views.presentation, name='presentation'),
    url(r'^leadership/$', views.people, name='people'),
    url(r'^join/$',views.join.as_view(),name='join'),
    url(r'^register/(?P<hash>[\w=]+)/$', views.staff_register, name="register"),
]
