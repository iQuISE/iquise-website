# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from django.contrib.auth.models import User
from members.models import Person

# REF: https://github.com/MasonM/django-elect

class Election(models.Model):
    pass

class Ballot(models.Model):
    election = models.ForeignKey(Election, related_name="ballots")
    seats_available = models.PositiveSmallIntegerField()
    write_in_available = models.BooleanField(default=True)

class Candidate(models.Model):
    pass

class Vote(models.Model):
    pass