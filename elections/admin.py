# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from elections.models import Election, Ballot, Voter, Nominee, Candidate

admin.site.register(Election)
admin.site.register(Ballot)
admin.site.register(Voter)
admin.site.register(Nominee)
admin.site.register(Candidate)