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
    supp_url = models.CharField(max_length=200)
    date = models.DateTimeField('date published')