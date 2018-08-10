# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

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

    def __str__(self):
        return self.title


class Person(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    school_status = models.CharField(max_length=200)
    profile_image_url = models.CharField(max_length=200)
    further_info_url = models.CharField(default=None, blank=True, max_length=200)

    def __str__(self):
        return self.name
