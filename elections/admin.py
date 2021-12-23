# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import StringIO

from django.http import HttpResponse
from django.contrib import admin

from elections.models import Election, Ballot, Voter, Candidate, get_current_election
from elections.forms import BallotForm

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
    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type=mimetype)
    response['Content-Disposition'] = 'attachment;filename="voters.csv"'
    return response 
download_voters.short_description = "Download selected voters"

class BallotInline(admin.TabularInline):
    model = Ballot
    form = BallotForm
    extra = 0
    show_change_link = True
    can_delete = False
    exclude = ("introduction", )

class ElectionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "nomination_start", "vote_start")
    inlines = (BallotInline, )

class FilterByElection(admin.ModelAdmin):
    list_filter = ("election", )

class BallotAdmin(admin.ModelAdmin):
    form = BallotForm
    list_display = ("__str__", "position_number", "election")
    list_filter = ("election", )

    def get_form(self, request, obj=None, **kwargs):
        form = super(BallotAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['election'].initial = get_current_election()
        return form

class VoterAdmin(admin.ModelAdmin):
    actions = (download_voters,)
    list_filter = ("election", "has_voted")
    list_display = ("__str__", "has_voted")
    search_fields = ("user__username", "user__first_name", "user__last_name", "user__email")

class CandidateAdmin(admin.ModelAdmin):
    list_display = ("__str__", "ballot", "incumbent")
    list_filter = ("ballot__election",)

admin.site.register(Election, ElectionAdmin)
admin.site.register(Ballot, BallotAdmin)
admin.site.register(Voter, VoterAdmin)
admin.site.register(Candidate, CandidateAdmin)
# We specifically don't want an admin interface for Vote or Nominee