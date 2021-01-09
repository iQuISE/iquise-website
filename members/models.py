# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import functools
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.urls import reverse
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save, pre_save

from iquise.utils import AlwaysClean

def get_current_term_start(*args, **kwargs):
    """*args and **kwargs passed to timedelta if supplied.
    
    Timedelta with no arguments is identity.
    """
    term = Term.objects.first()
    if term:
        return term.start + timedelta(*args, **kwargs)

def get_active_term():
    return Term.objects.filter(start__lte=timezone.now().date()).first()

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

class Person(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    # Rest are optional
    email = EmailIField(max_length=254,blank=True,help_text='Please use your university email if possible.')
    year = models.CharField(max_length=10,blank=True,help_text='Sophomore, Graduate Year #, Postdoc, Professor, etc.')
    school = models.ForeignKey('School', blank=True, null=True)
    lab = models.CharField(max_length=200,blank=True)
    subscribed = models.BooleanField(default=False,help_text='iquise-associates@mit.edu')

    def validate_unique(self, exclude=None):
        if self.email:
            qs = Person.objects.exclude(pk=self.pk).filter(email=self.email)
            if qs.exists():
                raise ValidationError(
                    mark_safe({
                        'email': '%s matches an existing user\'s email<br/>(contact <a href="mailto:iquise-exec@mit.edu">iquise-exec@mit.edu</a> for further assistance).'%self.email
                    })
                )

    class Meta:
        ordering = ['-last_name','-first_name']
        verbose_name_plural = u'\u200b'*5+u'People' # unicode invisible space to determine order (hack)
    
    def __unicode__(self):
        return u'%s, %s'%(self.last_name.capitalize(), self.first_name.capitalize())

# User/Group extention (staff)
class Profile(models.Model):
    # This is for the staff users only
    user = models.OneToOneField(User, models.CASCADE)
    affiliation = models.CharField(max_length=200,blank=True)
    profile_image = models.ImageField(upload_to='staff_profiles',blank=True)
    further_info_url = models.URLField(blank=True, max_length=200)
    linkedin_url = models.URLField(blank=True, max_length=200)
    facebook_url = models.URLField(blank=True, max_length=200)
    twitter_url = models.URLField(blank=True, max_length=200)

    def __unicode__(self):
        return self.user.get_full_name()

# Create Profile when user created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if not instance.is_superuser:
        if created:
            Profile.objects.create(user=instance)
        else:
            instance.profile.save()

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
        this = self
        while this:
            if this.contact_email:
                return this.contact_email
            this = this.parent.committee
        return None

    def clean(self):
        ancestor = self.parent
        while ancestor:
            if self.group == ancestor:
                raise ValidationError({"parent": "Parent cannot be the committee itself or any ancestor."})
            ancestor = ancestor.committee.parent

    def get_positions_held(self, term):
        posheld = PositionHeld.objects.filter(position__in=self.group.positions.all())
        posheld = posheld.filter(start__gte=term.start)
        stop = term.get_end()
        if stop:
            posheld = posheld.filter(start__lt=stop)
        return posheld

    def __unicode__(self):
        return "%s info" % self.group

# TODO: consider hiding explicit index, and use orderable UI: https://djangosnippets.org/snippets/1053/
class Position(models.Model):
    # TODO: committee should be renamed to "group" for less confusion
    DEFAULT_NAME = "" # Changing this will require updating old records too
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
            return "%s %s" % (self.committee, self.name)
        return unicode(self.committee)

# Make default position when group created
@receiver(post_save, sender=Group)
def make_default_position(sender, instance, created, **kwargs):
    if created:
         # Max "safe" index: https://docs.djangoproject.com/en/3.1/ref/models/fields/#positivesmallintegerfield
        Position.objects.create(name=Position.DEFAULT_NAME, committee=instance, index=32767)

# TODO: Integrate more tightly with Auth groups. Would be nice to use start/stop to
# define *which* groups the user is *currently* in.
class PositionHeld(AlwaysClean):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start = models.DateField(default=get_current_term_start)
    stop = models.DateField(null=True, blank=True)

    def clean(self, *args, **kwargs):
        if self.stop and self.stop <= self.start:
            raise ValidationError({"stop": "Stop date must be larger than start date."})
        if not Term.objects.filter(start__lte=self.start).exists():
            url = reverse('admin:members_term_add')+"?_popup=1"
            class_ = "related-widget-wrapper-link"
            msg = "No term overlaps with specified start date. Add one <a class='%s' href='%s'>here.</a>" % (class_, url)
            raise ValidationError({"start": mark_safe(msg)})
        if self._overlaps():
            raise ValidationError("This date range overlaps with another of the same position held for this user.")
        super(PositionHeld, self).clean(*args, **kwargs)

    def _overlaps(self):
        """Inclusive date range."""
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
        return self.id == get_active_term().id
    is_active.boolean = True

    def get_end(self):
        next_term = Term.objects.filter(start__gt=self.start).first()
        if next_term:
            return next_term.start
        return None

    def __unicode__(self):
        return self.start.isoformat()

    class Meta:
        ordering = ["-start"]
     