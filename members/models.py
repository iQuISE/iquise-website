# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save, pre_save

from iquise.utils import AlwaysClean

def term_beginning():
    last_term = Term.objects.first()
    return getattr(last_term, "end", None)

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

    def __unicode__(self):
        return self.user.get_full_name()

# Create Profile when user created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        Profile.objects.create(user=instance)

# Save Profile when user created
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not instance.is_superuser:
        instance.profile.save()

class Term(AlwaysClean):
    beginning = models.DateField(default=term_beginning)
    end = models.DateField()

    def clean(self, *args, **kwargs):
        if Term.objects.exclude(id=self.id).filter(beginning__lt=self.end).filter(end__gt=self.beginning).count():
            ValidationError("Term currently overlaps with another existing term.")
        super(Term, self).clean(*args, **kwargs)

    class Meta:
        ordering = ("-end",)

    def __unicode__(self):
        return "%s to %s"%(self.beginning.isoformat(), self.end.isoformat())

# TODO: consider hiding explicit index, and use orderable UI: https://djangosnippets.org/snippets/1053/
class Position(models.Model):
    committee = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="positions")
    name = models.CharField(max_length=50)
    users = models.ManyToManyField(User, through="PositionHeld")
    index = models.SmallIntegerField(default=0, help_text="Order to render on page.")

    class Meta:
        unique_together = (("committee", "index"), ("committee", "name"))

    def __unicode__(self):
        return "%s %s" % (self.committee, self.name)

class CommitteeRelation(AlwaysClean):
    start = models.DateField(default=timezone.localdate)
    stop = models.DateField(null=True, blank=True)

    def clean(self, *args, **kwargs):
        if self.stop and self.stop <= self.start:
            raise ValidationError({"stop": "Stop date must be larger than start date."})
        super(CommitteeRelation, self).clean(*args, **kwargs)

    class Meta:
        abstract = True

class PositionHeld(CommitteeRelation):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Positions Held"

# TODO: Integrate more tightly with Auth groups. Would be nice to use start/stop to
# define *which* groups the user is *currently* in.
class CommitteeMembership(CommitteeRelation):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="committees")
    committee = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="users")

    @property
    def terms(self):
        return Term.objects.filter(beginning__lte=self.start).filter(end__gte=self.stop)

    class Meta:
        unique_together = ("user", "committee")

    def __unicode__(self):
        return "%s, %s" % (self.user, self.committee)