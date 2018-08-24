# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.urls import reverse
from django.template.defaultfilters import slugify

def user_new_unicode(self):
    return self.username if self.get_full_name() == "" else self.get_full_name()
User.__unicode__ = user_new_unicode

# Helpers
class EmailIField(models.EmailField):
    # Case-insensitive email field
    def clean(self,*args,**kwargs):
        value = super(EmailIField,self).clean(*args,**kwargs)
        return value.lower()

def get_default_room():
    iq = IQUISE.objects.all()
    if iq:
        return unicode(iq[0].default_location)
    else:
        return None
def get_default_time():
    iq = IQUISE.objects.all()
    if iq:
        dt = timezone.now()
        dt = dt.replace(hour=iq[0].default_time.hour,minute=iq[0].default_time.minute,second=0,microsecond=0)
        return dt
    else:
        return None

 # Models
class IQUISE(models.Model):
    # Admin will limit this to a single entry. Used for website config
    description = models.TextField(max_length=2000)
    default_location = models.CharField(default='MIT Room 26-214',max_length=200)
    default_time = models.TimeField()

    class Meta:
        verbose_name = 'iQuISE'
        verbose_name_plural = u'\u200b'+u'iQuISE' # unicode invisible space to determine order (hack)

    def __unicode__(self):
        return u'iQuISE (%s)'%self.default_location

class Donor(models.Model):
    name = models.CharField(max_length=50,unique=True)
    affiliation = models.CharField(max_length=50,blank=True)
    def __unicode__(self):
        if self.affiliation:
            return u'%s (%s)'%(self.name,self.affiliation)
        else:
            return u'%s'%self.name

class Donation(models.Model):
    donor = models.ForeignKey('Donor')
    date = models.DateField()
    amount = models.PositiveIntegerField()
    class Meta:
        ordering = ['-date']
    def __unicode__(self):
        return unicode(self.amount)

# Scheduling models
class Session(models.Model):
    title = models.CharField(max_length=50,help_text='Label for the session, e.g. "Fall 2018"',unique=True)
    start = models.DateField()
    stop = models.DateField()
    slug = models.SlugField(help_text="Appears in URLs")

    @staticmethod
    def acvite_session():
        sessions = Session.objects.filter(stop__gte=timezone.now()).order_by('start')
        if sessions: return sessions[0]
        else: return None

    class Meta:
        ordering = ['-start']
        verbose_name = 'Session'
        verbose_name_plural = u'\u200b'*2+u'Sessions (event organizer)' # unicode invisible space to determine order (hack)
    def save(self,*args,**kwargs):
        if not self.id:
            self.slug = slugify(self.title)
        super(Session, self).save(*args,**kwargs)
    def __unicode__(self):
        return unicode(self.title)

class Event(models.Model):
    session = models.ForeignKey('Session')
    date = models.DateTimeField(default=get_default_time)
    location = models.CharField(default=get_default_room,max_length=200)
    audience = models.ManyToManyField('Person',blank=True)
    cancelled = models.BooleanField(default=False)
    class Meta:
        ordering = ['date']
    def clean(self):
        if not (self.date.date() >= self.session.start and self.date.date() <= self.session.stop):
            raise ValidationError(
                'Event date outside session date range!'
            )
            return super(Event,self).clean()
    def __unicode__(self):
        n_pres = self.presentation_set.all().count()
        n_confirmed = self.presentation_set.filter(confirmed=True).count()
        plural = 's' if n_pres != 1 else ''
        # Use the bracket session id to return to admin for that session upon delete
        return u'%s (%i presentation%s, %i confirmed, [%i])'%(self.date.date(),n_pres,plural,n_confirmed,self.session.id)

class Presenter(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    affiliation = models.CharField(max_length=200)
    profile_image_url = models.URLField(max_length=200,blank=True)

    def validate_unique(self, exclude=None):
        # Case-insensitive first and last name
        conflict = Presenter.objects.filter(first_name__iexact=self.first_name).filter(last_name__iexact=self.last_name).exclude(id=self.id)
        if conflict.exists():
            raise ValidationError('There is already a presenter with this name.')
    class Meta:
        ordering = ['last_name','first_name']
        verbose_name_plural = u'\u200b'*4+u'Presenters' # unicode invisible space to determine order (hack)
    def __unicode__(self):
        return u'%s, %s'%(self.last_name,self.first_name)

class Presentation(models.Model):
    # Talk theme
    THEORY = 'THEORY'
    EXPERIMENTAL = 'EXPERIMENT'
    THEME_CHOICES = (
        (EXPERIMENTAL,'Experimental'),
        (THEORY,'Theoretical'),
    )
    DEFAULT = 'TBD'
    event = models.ForeignKey('Event',models.SET_NULL,null=True,blank=True)
    presenters = models.ManyToManyField('Presenter')
    title = models.CharField(max_length=200,default=DEFAULT)
    short_description = models.CharField(max_length=500, default=DEFAULT)
    long_description = models.TextField(max_length=10000, default=DEFAULT)
    supp_url = models.URLField('supplemental url', blank=True, max_length=200)
    theme = models.CharField(max_length=20,choices=THEME_CHOICES,default=EXPERIMENTAL)
    confirmed = models.BooleanField(default=False)

    primary_contact = models.ForeignKey(User,limit_choices_to={'is_superuser': False})  # Will set default in admin.py

    def get_presenters(self):
        presenters = [str(p) for p in self.presenters.all()]
        return u', '.join(presenters)

    class Meta:
        verbose_name_plural = u'\u200b'*3+u'Presentations' # unicode invisible space to determine order (hack)
        ordering = ['-event__date']
    def validate_unique(self, exclude=None):
        # Should only be one confirmed presentation per event
        if hasattr(self.event,'presentation_set'):
            conflict = self.event.presentation_set.filter(confirmed=True).exclude(id=self.id)
            if conflict.exists():
                raise ValidationError(
                    mark_safe('There is already a confirmed talk for this event: <a href="%s">%s<\\a>'%(reverse('website:presentation',conflict.id),conflict.title))
                )
    def __unicode__(self):
        confirmed = 'confirmed' if self.confirmed else 'unconfirmed'
        return u'%s (%s)'%(self.title,confirmed)

# Audience models
class School(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        verbose_name_plural = u'\u200b'*6+u'Schools' # unicode invisible space to determine order (hack)
    def __unicode__(self):
        return unicode(self.name)

class Department(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        verbose_name_plural = u'\u200b'*7+u'Departments' # unicode invisible space to determine order (hack)
    def __unicode__(self):
        return unicode(self.name)

class Person(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    # Rest are optional
    email = EmailIField(max_length=254,blank=True)
    MIT_ID = models.PositiveIntegerField(null=True,blank=True,verbose_name='MIT ID')
    year = models.CharField(max_length=10,blank=True,help_text='Sophomore, Graduate Year #, Postdoc, Professor, etc.')
    department = models.ForeignKey('Department', blank=True, null=True)
    school = models.ForeignKey('School', blank=True, null=True)
    lab = models.CharField(max_length=200,blank=True)
    subscribed = models.BooleanField(default=False,help_text='iquise-associates@mit.edu')
    MANUAL = 'manual'
    WEBSITE = 'website'
    MOIRA = 'moira'
    ID = 'id'
    JOIN_CHOICES = (
        (MANUAL,'Manual Entry'),
        (WEBSITE,'Requested on Website'),
        (MOIRA,'Joined through Moira'),
        (ID,'MIT ID'),
    )
    join_method = models.CharField(max_length=20,choices=JOIN_CHOICES,default=MANUAL)

    def validate_unique(self, exclude=None):
        if self.email:
            qs = Person.objects.exclude(pk=self.pk).filter(email=self.email)
            if qs.exists():
                raise ValidationError(
                    mark_safe('%s matches an existing user\'s email<br/>(contact <a href="mailto:iquise-leadership@mit.edu">iquise-leadership@mit.edu</a> for further assistance).'%self.email)
                )

    class Meta:
        ordering = ['-last_name','-first_name']
        verbose_name_plural = u'\u200b'*5+u'People' # unicode invisible space to determine order (hack)
    def __unicode__(self):
        return u'%s, %s'%(self.last_name.capitalize(),self.first_name.capitalize())

# User extention (staff)
class Profile(models.Model):
    # This is for the staff users only
    user = models.OneToOneField(User, models.CASCADE)
    role = models.CharField(max_length=200,blank=True)
    school_status = models.CharField(max_length=200,blank=True)
    profile_image_url = models.URLField(max_length=200,blank=True)
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
