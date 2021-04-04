# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime

from django.test import TestCase
from elections.models import Election, Voter, Ballot, Nominee, Candidate, Vote

class BaseTestCase(TestCase):
    def setUp(self):
        user_model = apps.get_model(settings.DJANGO_ELECT_USER_MODEL)
        self.users = [
            user_model.objects.create_user(username="user1",
                email="user1@foo.com")
            user_model.objects.create_user(username="user2",
                email="user2@foo.com")
        ]
        self.election_current = Election.objects.create(
            name="current",
            introduction="Intro1",
            nomination_introduction="Nom_Intro1",
            nomination_start=datetime(2020, 0, 1),
            nomination_end=datetime(2020, 0, 8),
            vote_start=datetime(2020, 0, 10),
            vote_end=datetime(2020, 0, 17)
        )
        self.voters = [
            Voter.objects.create(election=self.election_current, user)
            for user in self.users
        ]
        self.election_current.add(self.users)

    def create_candidate(self, ballot, last_name='bar'):
        return ballot.candidates.create(
            first_name="foo",
            last_name=last_name,
            incumbent=incumbent)

    def create_current_ballot(self):
        return self.election_current.ballots.create()

class TestVotes(BaseTestCase):
    def test_cast_vote(self):
        pass

    def test_unique_votes(self):
        pass

    def test_no_CRUD_audit(self):
        pass

def TestElection(BaseTestCase):
    def test_current_election(self):
        pass

    def test_nomination_period(self):
        pass

    def test_voting_period(self):
        pass
    
    def test_results(self):
        pass