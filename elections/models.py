# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# REF: https://github.com/MasonM/django-elect
# TODO: convert introduction fields to use markdown

def get_current_election():
    now = timezone.now()
    election = Election.objects.filter(nomination_start__lte=now).filter(vote_end__gte=now)
    n = election.count()
    if n > 1:
        raise ValueError("Database contains multiple active elections.")
    if n == 1:
        return election[0]
    return None

class Election(models.Model):
    """Represents a single election.

    Elections will generally consist of many ballots (e.g. one for President, Vice
    President, etc.) which in turn will have multiple candidates.
    """
    name = models.CharField(max_length=127, blank=False, unique=True,
        help_text="Used to uniquely identify elections. Will be shown "+\
        "with ' Election' appended to it on all publicly-visible pages.")
    introduction = models.TextField(blank=True,
        help_text="This is printed at the top of the voting page below "+\
        "the header. Enter the text as HTML.")
    nomination_introduction = models.TextField(blank=True,
        help_text="This is printed at the top of the nomination page below "+\
        "the header. Enter the text as HTML.")
    nomination_start = models.DateTimeField(help_text="Start of nominations")
    nomination_end = models.DateTimeField(help_text="End of nominations")
    vote_start = models.DateTimeField(help_text="Start of voting")
    vote_end = models.DateTimeField(help_text="End of voting")
    allowed_voters = models.ManyToManyField(User, through="Voter")

    def __unicode__(self):
        return self.name

class Voter(models.Model):
    """We can store a token to send a unique email to users so we don't require login.

    Once used, this token should be removed to avoid re-use if so desired.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    election = models.ForeignKey("Election", on_delete=models.CASCADE)
    token = models.CharField(max_length=10) # base64, is more than enough

    class Meta:
        # There should be no duplicate tokens (or users) in an election!
        unique_together=(("election", "token"), ("election", "user"))

    def __str__(self):
        return str(self.user)


class Ballot(models.Model):
    """A ballot is associated with a single position and is associated with multiple candidates."""
    election = models.ForeignKey(Election, related_name="ballots")
    position_number = models.PositiveSmallIntegerField(default=1,
        help_text="Change this if you want to customize the order in which "+\
        "ballots are shown for an election.")
    description = models.CharField(max_length=255, blank=True)
    introduction = models.TextField(blank=True,
        help_text="If this field is non-empty, it will be shown below the "+\
        "ballot header on the voting page. Enter the text as HTML.")
    # TODO: if we ever want to elect general committee members:
    # seats_available = models.PositiveSmallIntegerField(default=1)

    def __unicode__(self):
        return "%s: %s" %(self.election, self.description)

class Nominee(models.Model):
    """A nominee is someone considered for a set of ballots, but unconfirmed.

    A nominee should transition to a candidate upon confirmation by the election
    committee. This will require all confirmed nominees to have a User account
    which will give us the profile to access basic bio data and a portrait.
    """
    ballots = models.ManyToManyField(Ballot, help_text="You may select as many as you'd like.") # TODO: limit_choices_to=ballots of current election?
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(help_text="MIT email address if available")
    nominator = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name="nominees")

class Candidate(models.Model):
    """A candidate is someone that appears on a particular ballot.
    
    A candidate running for multiple ballots will need separate candidate entries
    since there ballot-specific info may be different.
    """
    ballot = models.ForeignKey(Ballot, related_name="candidates")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    info = models.TextField(blank=True)
    incumbent = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s (%s)" % (user, ballot)

    class Meta:
        unique_together = ("ballot", "user") # Can only be on a ballot once!

class Vote(models.Model):
    pass