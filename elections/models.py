# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import random
import collections
import itertools

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from website.models import AbstractToken
# REF: https://github.com/MasonM/django-elect
# TODO: convert introduction fields to use markdown

def get_current_election(_now=None):
    now = _now or timezone.now()
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

    def get_results(self):
        return {ballot.description: ballot.get_results() for ballot in self.ballots.all()}

    def get_nominees(self):
        return {ballot.description: ballot.get_nominees() for ballot in self.ballots.all()}

    class Meta:
        ordering = ("-vote_start",)

    def __unicode__(self):
        return unicode(self.name)

class Voter(AbstractToken):
    """We can store a token to send a unique email to users so we don't require login.

    Once used, this token should be removed to avoid re-use if so desired.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    election = models.ForeignKey("Election", on_delete=models.CASCADE)
    has_voted = models.BooleanField(default=False)

    class Meta:
        # There should be no duplicate tokens (or users) in an election!
        unique_together=(("election", "user"), )

    def __unicode__(self):
        return unicode(self.user)


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

    def get_candidates_randomly(self):
        """Return list of candidates in random order.
        
        Different than getting via many-to-many manager, as this will evaluate
        the whole candidate queryset before returning.
        """
        c = list(self.candidates.all())
        random.shuffle(c)
        return c

    def get_votes(self):
        """Returns Dict[voter_id, List[Candidate]]"""
        casted_votes = collections.defaultdict(list)
        for vote in Vote.objects.filter(candidate__ballot=self).order_by("rank"):
            casted_votes[vote.voter_id].append(vote.candidate)
        return casted_votes

    def get_results(self):
        # The type "Vote" is just a List[Candidate]; this is how we keep track of preference
        # rounds: List[Dict[Candidate, List[Vote]]]
        rounds = [collections.defaultdict(list)]
        uncounted_votes = self.get_votes().values() # We don't care about voter_id
        for i in itertools.count():
            if not uncounted_votes:
                break
            for vote in uncounted_votes:
                if len(vote) > 0:
                    rounds[i][vote[0]].append(vote)
            tallies = map(len, rounds[i].values())
            if any([t > sum(tallies)/2.0 for t in tallies]):
                break # We're done when a candidate has a majority
            # Eliminate lowest and continue to next round
            lowest_tally = min(tallies)
            uncounted_votes = []
            eliminated = []
            next_round = collections.defaultdict(list) # There could be candidates not seen in first round still
            for cand, votes in rounds[i].items():
                if len(votes) == lowest_tally:
                    uncounted_votes += votes
                    eliminated.append(cand)
                else: # Copy over from last round
                    next_round[cand] = votes[:]
            rounds.append(next_round)
            # Prune uncounted_votes of eliminated candidates
            exhausted_votes = [] # No more preferential candidates in vote
            for vote in uncounted_votes:
                for eliminated_cand in eliminated:
                    if eliminated_cand in vote:
                        vote.remove(eliminated_cand)
                        if len(vote) == 0:
                            exhausted_votes.append(vote)
            for vote in exhausted_votes:
                uncounted_votes.remove(vote)
        # Finalize by counting votes in a normal serializable dict
        for i in range(len(rounds)):
            rounds[i] = {"%s (id=%i)" % (key, key.id): len(val) for key, val in rounds[i].items()}
        return rounds

    def get_nominees(self):
        """Get nominees in dictionary by email."""
        nominees = collections.defaultdict(list)
        for nominee in Nominee.objects.filter(ballots=self):
            nominees[nominee.email].append(str(nominee))
        return dict(nominees)

    class Meta:
        ordering = ("position_number",)

    def __unicode__(self):
        return unicode(self.description)

def get_ballots_for_current_election(_now=None):
    return {"election": get_current_election(_now)}

class Nominee(models.Model):
    """A nominee is someone considered for a set of ballots, but unconfirmed.

    A nominee should transition to a candidate upon confirmation by the election
    committee. This will require all confirmed nominees to have a User account
    which will give us the profile to access basic bio data and a portrait.
    """
    ballots = models.ManyToManyField(Ballot,
        limit_choices_to=get_ballots_for_current_election,
        help_text="You may select as many as you'd like. (Hold Shift or ⌘ to select multiple)"
    )
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(help_text="MIT email address if available")
    nominator = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name="nominees")

    def __unicode__(self):
        return u"%s %s" % (self.first_name, self.last_name)

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
        return unicode(self.user)

    class Meta:
        unique_together = ("ballot", "user") # Can only be on a ballot once!

class Vote(models.Model):
    """A single vote cast for a candidate on a ballot."""
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name="votes")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="votes")
    rank = models.PositiveSmallIntegerField(default=0)
    submitted = models.DateTimeField(auto_created=True, null=True) # This model is excluded from standard audit
    ip = models.GenericIPAddressField(blank=True, null=True)

    def __unicode__(self):
        return u"%s: %i" % (self.candidate, self.rank)

    class Meta:
        unique_together = ("voter", "candidate")