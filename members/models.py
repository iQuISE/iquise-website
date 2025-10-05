# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import functools
from datetime import timedelta
from django.forms.fields import CharField

from easyaudit.models import CRUDEvent

from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save, pre_save
from django.contrib.contenttypes.models import ContentType

from iquise.utils import AlwaysClean, mail_admins, send_mail
from members.tokens import email_confirmation_token

def get_current_term_start(*args, **kwargs):
    """*args and **kwargs passed to timedelta if supplied.
    
    Timedelta with no arguments is identity.
    """
    term = Term.objects.first()
    if term:
        return term.start + timedelta(*args, **kwargs)

def get_term_containing(date=None):
    """Get the term containing ``date``. If no ``date`` supplied, returns active term."""
    date = date or timezone.now().date()
    # Term should already be ordered (see Term.Meta.ordering)
    return Term.objects.filter(start__lte=date).first()

class EmailIField(models.EmailField):
    # Case-insensitive email field
    def clean(self,*args,**kwargs):
        value = super(EmailIField,self).clean(*args,**kwargs)
        return value.lower()

class School(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        verbose_name_plural = u'\u200b'*6+u'Schools' # unicode invisible space to determine order (hack)
    
    def __unicode__(self):
        return unicode(self.name)

class ValidEmailDomain(AlwaysClean):
    STATUS_CHOICES = (
        ('u', 'Unreviewed'),
        ('a', 'Accepted'),
        ('d', 'Denied'),
    )
    domain = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="a",
        help_text=(
            "Accepted means users may enter with this domain or any subdomain. "
            "Denied will disallow submission of requests under this domain or subdomain. "
            "The most specific subdomain is used. "
            "Unverified is used to automatically add new domains that haven't been seen yet (these are ignored during validation)."
        )
    )
    hits = models.PositiveIntegerField(default=0, help_text="Number of emails whose fate was decided by this entry.")

    class Meta:
        ordering = ("-hits", )

    @staticmethod
    def order_by_domain_level(rows, reversed=False):
        s = -1 if reversed else 1
        return sorted(rows, key=lambda row: s*len(row.domain.split(".")))

    def clean(self):
        self.domain = self.domain.lower().strip(".")
        if not self.domain:
            raise ValidationError({'domain': 'Empty domains not accepted.'})
        return super(ValidEmailDomain,self).clean()

    @property
    def is_valid(self):
        return self.status == "a"

    @classmethod
    def get_domain(cls, addr):
        """Get the domain or return None."""
        # TODO: could probably cache this since it won't change often
        rows = cls.objects.all()
        addr = addr.lower()
        for row in cls.order_by_domain_level(rows, reversed=True):
            if addr.endswith(row.domain):
                row.hits += 1
                row.save()
                if row.status == "u": # We want to count the hit but ignore if unreviewed
                    continue
                return row
        return None

    @staticmethod
    def new_domain_request(user, request):
        domain_str = user.email.split("@")[-1].lower()
        domain, _ = ValidEmailDomain.objects.get_or_create(domain=domain_str, status="u")
        # Email admins for quick review
        msg = (
            "A request to join the community was received from an unverified domain:\n"
            "%s (profile: %s) \n\n"
            "You should reply to this user directly if you choose to deny this request. "
            "An email has been sent to them to confirm this address.\n\n"
            "You can approve/deny emails from this domain by updating its entry:\n%s"
        ) % (
            user.email,
            request.build_absolute_uri(reverse('admin:auth_user_change', args=[user.id])),
            request.build_absolute_uri(reverse('admin:members_validemaildomain_change', args=[domain.id])),
        )
        mail_admins("New Domain Request", msg, user=request.user)


    def __unicode__(self):
        return self.domain

class EmailList(models.Model):
    address = EmailIField(unique=True)
    # description = CharField(max_length=100, empty=True)

    def __unicode__(self):
        return unicode(self.address)

SUBSCRIPTION_DISCLAIMER = (
    "We do need to manually verify subscriptions, so please bear with us. "
    "We are a volunteer organization and we're all grad students too!"
)
# User/Group extention (staff)
class Profile(models.Model):
    LEVELS = (
        ("0", "Highschool"), 
        ("1", "Undergraduate"),
        ("2", "Graduate"),
        ("3", "PostDoc"),
        ("4", "Professor"),
        ("5", "Professional"),
        ("9", "Retired"),
    )

    # This gets auto generated on user creation, so fields need to be able to be null
    user = models.OneToOneField(User, models.CASCADE)
    affiliation = models.CharField(max_length=200)
    profile_image = models.ImageField(upload_to='staff_profiles',blank=True)

    graduation_year = models.PositiveSmallIntegerField(null=True)
    level = models.CharField(max_length=2, choices=LEVELS, default="2")
    year = models.CharField(max_length=10, blank=True, help_text="DEPRECATED") # TODO: migrate this to grad year and level
    subscriptions = models.ManyToManyField(EmailList, blank=True, related_name="subscribers")
    subscription_requests = models.ManyToManyField(EmailList, blank=True, related_name="+",
        help_text=SUBSCRIPTION_DISCLAIMER
    )

    further_info_url = models.URLField(blank=True, max_length=200)
    linkedin_url = models.URLField(blank=True, max_length=200)
    facebook_url = models.URLField(blank=True, max_length=200)
    twitter_url = models.URLField(blank=True, max_length=200)

    email_confirmed = models.BooleanField(default=False)

    @property
    def datetime_joined(self):
        CRUDEvent.objects.get(
            event_type=CRUDEvent.CREATE,
            content_type=ContentType.objects.get_for_model(Profile),
            object_id=self.id,
        )

    @staticmethod
    def send_email_confirmation(user, request):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_confirmation_token.make_token(user)
        confirm_link = request.build_absolute_uri(
            reverse('members:confirm_email', kwargs={"uidb64": uid, "token": token})
        )
        msg = (
            "Thank you for making an account with iQuISE! "
            "We need to confirm your email address. "
            "If you did not register, you can ignore this email.\n\n"
            "Otherwise click this link below to confirm your email:\n%s"
        ) % confirm_link
        send_mail("[iQuISE] Validate Email Address", msg, recipient_list=[user.email], user=request.user)

    def __unicode__(self):
        return self.user.get_full_name()

# Create Profile when user created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Note, doing it this way allows us to get User.profile without worry at the
    # cost of an extra database hit each time we create a new User.
    if created:
        Profile.objects.get_or_create(user=instance)

class Committee(AlwaysClean):
    group = models.OneToOneField(Group, models.CASCADE)
    parent = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    description = models.TextField(
        max_length=500,
        blank=True,
        help_text=(
            "Short description here on first line (next line blank!)."
            "<br><br>Elaborate here if you need."
            "<br>Multiple lines if needed."
        )
    )
    contact_email = models.EmailField(blank=True, help_text="If blank, parent's email will be used if available.")
    show_email = models.BooleanField(default=True, help_text="If no self or parent Contact email; will not be displayed.")

    @property
    def short_description(self):
        lines = [ln.strip() for ln in self.description.strip().splitlines()]
        if not lines: # No text
            return ""
        try:
            sep = lines.index("")
        except ValueError: # No double newline
            return ""
        return " ".join(lines[:sep])

    @property
    def email(self):
        # An email may be returned even if show_email=False!
        this = self.group
        while this:
            if this.committee.contact_email:
                return this.committee.contact_email
            this = this.committee.parent
        return None

    def clean(self):
        ancestor = self.parent
        while ancestor:
            if self.group == ancestor:
                raise ValidationError({"parent": "Parent cannot be the committee itself or any ancestor."})
            ancestor = ancestor.committee.parent

    def get_positions_held(self, term):
        posheld = PositionHeld.objects.filter(position__in=self.group.positions.all())
        stop = None
        if term:
            posheld = posheld.exclude(stop__lte=term.start)
            stop = term.get_end()
        else: # Filter up to next term if it exists
            next_term = Term.objects.first()
            if next_term:
                stop = next_term.start
        if stop:
            posheld = posheld.filter(start__lt=stop)
        return posheld

    def __unicode__(self):
        return u"%s info" % self.group

# TODO: consider hiding explicit index, and use orderable UI: https://djangosnippets.org/snippets/1053/
class Position(models.Model):
    # TODO: committee should be renamed to "group" for less confusion
    DEFAULT_NAME = "" # Changing this will require updating old records too
    DEFAULT_INDEX = 32767 # Max "safe" index: https://docs.djangoproject.com/en/3.1/ref/models/fields/#positivesmallintegerfield
    
    committee = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="positions")
    name = models.CharField(max_length=50)
    users = models.ManyToManyField(User, through="PositionHeld")
    index = models.PositiveSmallIntegerField(default=0, help_text="Order to render on page.")

    class Meta:
        unique_together = (("committee", "index"), ("committee", "name"))
        ordering = ["committee", "index"]

    @staticmethod
    def exclude_default(qs):
        """Remove default from a queryset."""
        return qs.exclude(name=Position.DEFAULT_NAME)

    def is_default(self):
        return self.name == self.DEFAULT_NAME

    def __unicode__(self):
        if self.name:
            return u"%s %s" % (self.committee, self.name)
        return unicode(self.committee)

# Make default position when group created
@receiver(post_save, sender=Committee)
def make_default_position(sender, instance, created, **kwargs):
    # Note, in principle there is no need to make this in the database, but it is
    # convenient since everywhere else we no longer care about a default object...
    # it is just like every other position
    if created:
        Position.objects.create(name=Position.DEFAULT_NAME, committee=instance.group, index=Position.DEFAULT_INDEX)

# TODO: Integrate more tightly with Auth groups. Would be nice to use start/stop to
# define *which* groups the user is *currently* in.
class PositionHeld(AlwaysClean):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start = models.DateField(default=get_current_term_start)
    stop = models.DateField(null=True, blank=True)

    @property
    def title(self):
        if not self.position.is_default():
            return self.position.name

    @property
    def html_description(self):
        start = self.start.strftime(r"%m/%d/%Y")
        if self.stop:
            stop = self.stop.strftime(r"%m/%d/%Y")
        else:
            stop = "present"
        date_range = "%s - %s" % (start, stop)
        return mark_safe(u"%s<br>%s" % (date_range, self.user.profile.affiliation))

    def clean(self):
        if self.stop and self.stop <= self.start:
            raise ValidationError({"stop": "Stop date must be larger than start date."})
        if not Term.objects.filter(start__lte=self.start).exists():
            url = reverse('admin:members_term_add')+"?_popup=1"
            class_ = "related-widget-wrapper-link"
            msg = "No term overlaps with specified start date. Add one <a class='%s' href='%s'>here.</a>" % (class_, url)
            raise ValidationError({"start": mark_safe(msg)})

    def validate_unique(self, exclude=None):
        super(PositionHeld, self).validate_unique(exclude=exclude)
        # position may end up in exclude if user forgot to set it, so it will already error due to that
        # eventhough this code gets evaluated still
        if "position" not in exclude and self._overlaps():
            raise ValidationError("This date range overlaps with another of the same position held for this user.")

    def _overlaps(self):
        """Start/stop overlap ok."""
        qs = PositionHeld.objects.exclude(id=self.id).filter(user=self.user, position=self.position)
        qs = qs.exclude(stop__lte=self.start)
        if self.stop:
            qs = qs.exclude(start__gte=self.stop)
        return qs.exists() # Hit the db here

    class Meta:
        verbose_name_plural = "Positions Held"
        ordering = ["-start", "position"] # TODO: would be nice to -stop, but we would want nulls first

class Term(models.Model):
    start = models.DateField(
        default=functools.partial(get_current_term_start, days=365),
        help_text="This term will extend to the next term's start date.",
    )

    def is_active(self):
        active_term = get_term_containing()
        return active_term and self.id == active_term.id
    is_active.boolean = True

    def get_end(self):
        next_term = Term.objects.filter(start__gt=self.start).last()
        if next_term:
            return next_term.start
        return None

    def __unicode__(self):
        return unicode(self.start.isoformat())

    class Meta:
        ordering = ["-start"]
