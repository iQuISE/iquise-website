# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class IQUISE(models.Model):
    # Admin will limit this to a single entry
    description = models.TextField(max_length=2000)
    default_location = models.CharField(default='MIT Room 26-214',max_length=200)

    class Meta:
        verbose_name_plural = 'iQuISE'

    def __unicode__(self):
        return u'iQuISE'

class Presentation(models.Model):
    presenter = models.CharField(max_length=200)
    profile_image_url = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=500)
    long_description = models.CharField(max_length=10000)
    description_url = models.CharField(max_length=200)
    supp_url = models.CharField(default=None, blank=True, max_length=200)
    affiliation = models.CharField(max_length=200)
    date = models.DateTimeField('presentation date')
    location = models.CharField(default='MIT Room 26-214',max_length=200)

    def __unicode__(self):
        return u'%s (%s)'%(self.title,self.presenter)


class Person(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    school_status = models.CharField(max_length=200)
    profile_image_url = models.CharField(max_length=200)
    further_info_url = models.CharField(default=None, blank=True, max_length=200)

    def __unicode__(self):
        return self.name
