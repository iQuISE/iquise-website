# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core import mail
from django.test import TestCase

from members.models import User, ValidEmailDomain

JOIN_URL = "/join/"

class TestValidEmailSorting(TestCase):
    def test_sort_by_level(self):
        a = ValidEmailDomain(domain="a")
        b = ValidEmailDomain(domain="a.b")
        ordered = [a, b]
        self.assertEqual(ValidEmailDomain.order_by_domain_level([a, b]), ordered)
        self.assertEqual(ValidEmailDomain.order_by_domain_level([b, a]), ordered)

class TestValidEmail(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.good = ValidEmailDomain.objects.create(domain="good", status="a") # accept
        cls.badgood = ValidEmailDomain.objects.create(domain="bad.good", status="d") # deny

        cls.bad = ValidEmailDomain.objects.create(domain="bad", status="d") # deny
        cls.goodbad = ValidEmailDomain.objects.create(domain="good.bad", status="a") # accept

    def check_hit(self, row, n=1):
        row.refresh_from_db()
        self.assertEqual(row.hits, n)

    def test_accept_other_good(self):
        valid, repr = ValidEmailDomain.check_email("foo@other.good")
        self.assertTrue(valid)
        self.assertTrue(repr)
        self.check_hit(self.good)
        
    def test_deny_specific_bad(self):
        valid, repr = ValidEmailDomain.check_email("foo@bad.good")
        self.assertFalse(valid)
        self.assertTrue(repr)
        self.check_hit(self.badgood)

    def test_deny_specific_bad_sub(self):
        valid, repr = ValidEmailDomain.check_email("foo@other.bad.good")
        self.assertFalse(valid)
        self.assertTrue(repr)
        self.check_hit(self.badgood)

    def test_deny_other_bad(self):
        valid, repr = ValidEmailDomain.check_email("foo@other.bad")
        self.assertFalse(valid)
        self.assertTrue(repr)
        self.check_hit(self.bad)

    def test_accept_specific_good(self):
        valid, repr = ValidEmailDomain.check_email("foo@good.bad")
        self.assertTrue(valid)
        self.assertTrue(repr)
        self.check_hit(self.goodbad)

    def test_accept_specific_good_sub(self):
        valid, repr = ValidEmailDomain.check_email("foo@other.good.bad")
        self.assertTrue(valid)
        self.assertTrue(repr)
        self.check_hit(self.goodbad)

class TestJoin(TestCase):
    @classmethod
    def setUpTestData(cls):
        ValidEmailDomain.objects.create(domain="foo.bar", status="u") # un-reviewed
        cls.base_data = {
            "first_name": "foo",
            "last_name": "bar",
            "affiliation": "testing university",
            "graduation_year": 2021,
            "level": "Undergraduate",
        }
        cls.existing_user_email = "existing@foo.edu"
        User.objects.create(
            first_name="foo", last_name="bar",
            email=cls.existing_user_email,
            username=cls.existing_user_email,
        )

    def email_validate_email(self, msg, new_email):
        self.assertEqual(msg.to, [new_email])
        self.assertEqual(msg.from_email, "iquise-no-reply@rlehosting.mit.edu")
        self.assertEqual(msg.subject, "[iQuISE] Validate Email Address")

    def email_new_domain(self, msg):
        self.assertEqual(msg.to, ["iquise-web@mit.edu"])
        self.assertEqual(msg.from_email, "iquise-no-reply@rlehosting.mit.edu")
        self.assertEqual(msg.subject, "[iQuISE] New Domain Request")

    def test_accept_email_and_confirmed(self):
        email = "foobar@something.edu"
        data = {"email": email}
        data.update(self.base_data)
        response = self.client.post(JOIN_URL, data, follow=True)
        self.assertContains(response, "Submission received! Check your email to confirm your email address.")

        self.assertEqual(len(mail.outbox), 1)
        self.email_validate_email(mail.outbox[0], email)
        
        # Test user added
        self.assertFalse(User.objects.get(username=email).profile.email_confirmed)
        # Validate
        path = mail.outbox[0].body.splitlines()[-1]
        response = self.client.get(path, follow=True)
        self.assertContains(response, "Email confirmed!")
        # Test updated model
        self.assertTrue(User.objects.get(username=email).profile.email_confirmed)

        # Using link again
        response = self.client.get(path, follow=True)
        self.assertContains(response, "Email confirmed!")

    def test_unreviewed_email(self):
        email = "foobar@foo.bar"
        data = {"email": email}
        data.update(self.base_data)
        response = self.client.post(JOIN_URL, data, follow=True)
        self.assertContains(response, "Submission received! Check your email to confirm your email address.")

        self.assertEqual(len(mail.outbox), 2)
        self.email_new_domain(mail.outbox[0])
        self.email_validate_email(mail.outbox[1], email)

    def test_new_email(self): # TODO
        domain = "new.email"
        email = "foobar@"+domain
        self.assertFalse(ValidEmailDomain.objects.filter(domain=domain).exists())
        data = {"email": email}
        data.update(self.base_data)
        response = self.client.post(JOIN_URL, data, follow=True)
        self.assertContains(response, "Submission received! Check your email to confirm your email address.")

        self.assertEqual(len(mail.outbox), 2)
        self.email_new_domain(mail.outbox[0])
        self.email_validate_email(mail.outbox[1], email)

    def test_deny_email(self):
        data = {"email": "foobar@gmail.com"}
        data.update(self.base_data)
        response = self.client.post(JOIN_URL, data)
        self.assertContains(response, "Not recognized as a university address. Email us if you think this is a mistake.")
        self.assertEqual(len(mail.outbox), 0)

    def test_deny_email_subdomain(self):
        data = {"email": "foobar@sub.gmail.com"}
        data.update(self.base_data)
        response = self.client.post(JOIN_URL, data)
        self.assertContains(response, "Not recognized as a university address. Email us if you think this is a mistake.")
        self.assertEqual(len(mail.outbox), 0)

    def test_existing_email(self):
        data = {"email": self.existing_user_email}
        data.update(self.base_data)
        response = self.client.post(JOIN_URL, data)
        self.assertContains(response, "A user with this email already exists, email us for help.")