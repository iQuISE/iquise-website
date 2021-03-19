# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from elections.models import Election, Ballot, Voter, Nominee, Candidate


class ElectionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "nomination_start", "vote_start")

class BallotAdmin(admin.ModelAdmin):
    list_display = ("__str__", "position_number", "election")
    list_filter = ("election", )

class VoterAdmin(admin.ModelAdmin):
    list_filter = ("election", )

admin.site.register(Election, ElectionAdmin)
admin.site.register(Ballot, BallotAdmin)
admin.site.register(Voter, VoterAdmin)
admin.site.register(Nominee)
admin.site.register(Candidate)