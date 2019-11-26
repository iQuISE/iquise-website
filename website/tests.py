# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import *

class SeminarTodayBehavior(TestCase):
    def setUp(self):
        today = timezone.localtime()
        # Setup the session
        start = today - timedelta(months=6)
        stop = today + timedelta(months=6)
        session = Session.objects.create(title="TEST",
                                         start=start,
                                         stop=stop)
        # Add a presenter
        presenter = Presenter.objects.create(first_name='Foo',
                                             last_name='Bar',
                                             affiliation='MIT')
        # Create an event slot in session
        event = Event.objects.create(session=session
                                     date=today)


    def test_home_page(self):
        pass