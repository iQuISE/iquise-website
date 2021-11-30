# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from members.models import User, ValidEmailDomain, Profile, EmailList

class TestProfile(TestCase):
    def test_new_member_db(self):
        u = User.objects.create(username="test")
        self.assertTrue(hasattr(u, "profile"))
        # Check the admin page doesn't crash and burn
        resp = self.client.get(reverse("admin:auth_user_changelist"), follow=True)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse("admin:auth_user_change", args=[u.id]), follow=True)
        self.assertEqual(resp.status_code, 200)

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
        domain = ValidEmailDomain.get_domain("foo@other.good")
        self.assertTrue(domain.is_valid)
        self.check_hit(self.good)
        
    def test_deny_specific_bad(self):
        domain = ValidEmailDomain.get_domain("foo@bad.good")
        self.assertFalse(domain.is_valid)
        self.check_hit(self.badgood)

    def test_deny_specific_bad_sub(self):
        domain = ValidEmailDomain.get_domain("foo@other.bad.good")
        self.assertFalse(domain.is_valid)
        self.check_hit(self.badgood)

    def test_deny_other_bad(self):
        domain = ValidEmailDomain.get_domain("foo@other.bad")
        self.assertFalse(domain.is_valid)
        self.check_hit(self.bad)

    def test_accept_specific_good(self):
        domain = ValidEmailDomain.get_domain("foo@good.bad")
        self.assertTrue(domain.is_valid)
        self.check_hit(self.goodbad)

    def test_accept_specific_good_sub(self):
        domain = ValidEmailDomain.get_domain("foo@other.good.bad")
        self.assertTrue(domain.is_valid)
        self.check_hit(self.goodbad)

class TestJoin(TestCase):
    @classmethod
    def setUpTestData(cls):
        ValidEmailDomain.objects.create(domain="foo.bar", status="u") # un-reviewed
        email_list = EmailList.objects.get(address="iquise-associates@mit.edu")
        cls.base_data = {
            "first_name": "foo",
            "last_name": "bar",
            "affiliation": "testing university",
            "graduation_year": 2021,
            "level": "1",
            "subscriptions": [str(email_list.id)],
            "password1": "foobar123!",
            "password2": "foobar123!"
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
        self.email_new_domain(mail.outbox[1])
        self.email_validate_email(mail.outbox[0], email)

    def test_new_email(self): # TODO
        domain = "new.email"
        email = "foobar@"+domain
        self.assertFalse(ValidEmailDomain.objects.filter(domain=domain).exists())
        data = {"email": email}
        data.update(self.base_data)
        response = self.client.post(JOIN_URL, data, follow=True)
        self.assertContains(response, "Submission received! Check your email to confirm your email address.")

        self.assertEqual(len(mail.outbox), 2)
        self.email_new_domain(mail.outbox[1])
        self.email_validate_email(mail.outbox[0], email)

    def test_deny_email(self):
        data = {"email": "foobar@gmail.com"}
        data.update(self.base_data)
        response = self.client.post(JOIN_URL, data)
        self.assertContains(response, "Must use a university address to subscribe.")
        self.assertEqual(len(mail.outbox), 0)

    def test_deny_email_subdomain(self):
        data = {"email": "foobar@sub.gmail.com"}
        data.update(self.base_data)
        response = self.client.post(JOIN_URL, data)
        self.assertContains(response, "Must use a university address to subscribe.")
        self.assertEqual(len(mail.outbox), 0)

    def test_existing_email(self):
        data = {"email": self.existing_user_email}
        data.update(self.base_data)
        response = self.client.post(JOIN_URL, data)
        self.assertContains(response, "A user with this email already exists, email us for help.")

    def test_bad_email_no_subscription(self):
        data = {"email": "foobar@sub.gmail.com"}
        data.update(self.base_data)
        data["subscriptions"] = []
        response = self.client.post(JOIN_URL, data, follow=True)
        self.assertContains(response, "Submission received! Check your email to confirm your email address.")
