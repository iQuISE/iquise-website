# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import StringIO

from django.http import HttpResponse
from django.contrib import admin

from elections.models import Election, Ballot, Voter, Nominee, Candidate

def download_voters(modeladmin, request, queryset):
    def proc_row(row):
        out_row = [value.replace('"', '""') for value in row]
        output.write('"%s"\n' % '"\t"'.join(out_row))

    # TODO: Turn this into an emailer instead
    output = StringIO.StringIO()
    proc_row(["first name", "email", "token"])
    for voter in queryset:
        proc_row([voter.user.first_name, voter.user.email, voter.token])
           
    mimetype = 'text/csv'
    file_ext = 'csv'
    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type=mimetype)
    response['Content-Disposition'] = 'attachment;filename="voters.csv"'
    return response 
download_voters.short_description = "Download selected voters"

class ElectionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "nomination_start", "vote_start")

class BallotAdmin(admin.ModelAdmin):
    list_display = ("__str__", "position_number", "election")
    list_filter = ("election", )

class VoterAdmin(admin.ModelAdmin):
    list_filter = ("election", )
    actions = (download_voters,)

admin.site.register(Election, ElectionAdmin)
admin.site.register(Ballot, BallotAdmin)
admin.site.register(Voter, VoterAdmin)
admin.site.register(Nominee)
admin.site.register(Candidate)