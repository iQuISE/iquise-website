# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, hashlib
from StringIO import StringIO
from PIL import Image

from django.db import models
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.core.files.base import ContentFile

from members.models import Person

def user_new_unicode(self):
    return self.username if self.get_full_name() == "" else self.get_full_name()
User.__unicode__ = user_new_unicode

# Helpers
def get_default_room():
    iq = IQUISE.objects.all()
    if iq:
        return unicode(iq[0].default_location)
    else:
        return None
def get_default_time():
    iq = IQUISE.objects.all()
    if iq:
        dt = timezone.localtime()
        dt = dt.replace(hour=iq[0].default_time.hour,minute=iq[0].default_time.minute,second=0,microsecond=0)
        return dt
    else:
        return None

@deconstructible
class photo_path(object):
    def __init__(self,subdir):
        self.subdir = subdir

    def __call__(self, instance, filename):
        # Anonymize filenames (presenter is unique on (last_name, first_name) pair)
        _, ext = os.path.splitext(filename)
        # md5 hex digest is 128 bits, so should be 32 chars long
        name = (instance.first_name + instance.last_name).encode('utf-8')
        filename = hashlib.md5(name).hexdigest()
        # Django's storage class is cutting of full filename and appending its own random
        # chars at the end. This behavior is acceptable, but makes it a bit harder to use
        # above technique to locate a file based on instance first/last_name alone. 
        return os.path.join(self.subdir, filename + ext)

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

class EmbedEngine(models.Model):
    name = models.CharField(max_length=50,unique=True)
    html_template = models.TextField(help_text=r'Use {{ID}} which will get swapped in for the EmbeddedVideo.video_id.')
    url_help = models.CharField(max_length=100,blank=True,help_text='Used to help the user figure out where the video_id is.')

    def __unicode__(self):
        return u'%s: %s'%(self.name,self.url_help)

class EmbeddedVideo(models.Model):
    video_id = models.CharField(max_length=50)
    engine = models.ForeignKey('EmbedEngine',on_delete=models.PROTECT)
    public = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode(self.video_id)

# Scheduling models
class Session(models.Model):
    title = models.CharField(max_length=50,help_text='Label for the session, e.g. "Fall 2018"',unique=True)
    start = models.DateField()
    stop = models.DateField()
    slug = models.SlugField(help_text="Appears in URLs")

    @staticmethod
    def active_session():
        sessions = Session.objects.filter(stop__gte=timezone.localtime()).order_by('start')
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
    audience = models.ManyToManyField(Person,blank=True)
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
    profile_image = models.ImageField(upload_to=photo_path('presenters'),blank=True)
    profile_image_thumb = models.ImageField(upload_to=photo_path('thumbs'),blank=True,editable=False)

    def validate_unique(self, exclude=None):
        # Case-insensitive first and last name
        conflict = Presenter.objects.filter(first_name__iexact=self.first_name).filter(last_name__iexact=self.last_name).exclude(id=self.id)
        if conflict.exists():
            raise ValidationError('There is already a presenter with this name.')
    class Meta:
        ordering = ['last_name','first_name']
        verbose_name_plural = u'\u200b'*4+u'Presenters' # unicode invisible space to determine order (hack)
    def save(self):
        # Add thumbnail (if provided)
        force_update = False
        if self.profile_image:
            max_size = (300,600)
            #Original photo
            imgFile = Image.open(StringIO(self.profile_image.read()))
            #Convert to RGB
            if imgFile.mode not in ('L', 'RGB'):
                imgFile = imgFile.convert('RGB')
            #Save thumbnail
            working = imgFile.copy()
            working.thumbnail(max_size,Image.ANTIALIAS)
            fp = StringIO()
            working.save(fp,'JPEG', quality=95)
            working.seek(0)
            cf = ContentFile(fp.getvalue())
            name, _ = os.path.splitext(self.profile_image.name)
            self.profile_image_thumb.save(name=name + '.jpg',content=cf,save=False)
            if self.id:
                force_update = True # Maintain DB integrity
        super(Presenter, self).save(force_update=force_update)

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
    event = models.ManyToManyField('Event',blank=True)
    presenters = models.ManyToManyField('Presenter')
    title = models.CharField(max_length=200,default=DEFAULT)
    short_description = models.CharField(max_length=500, default=DEFAULT)
    long_description = models.TextField(max_length=10000, default=DEFAULT)
    supp_url = models.URLField('supplemental url', blank=True, max_length=200)
    theme = models.CharField(max_length=20,choices=THEME_CHOICES,default=EXPERIMENTAL)
    confirmed = models.BooleanField(default=False)
    video = models.ForeignKey('EmbeddedVideo',blank=True,null=True,on_delete=models.SET_NULL)

    primary_contact = models.ForeignKey(User,limit_choices_to={'is_superuser': False})  # Will set default in admin.py

    def get_presenters(self):
        presenters = [unicode(p) for p in self.presenters.all()]
        return u', '.join(presenters)

    class Meta:
        verbose_name_plural = u'\u200b'*3+u'Presentations' # unicode invisible space to determine order (hack)
        ordering = ['-event__date']

    def __unicode__(self):
        confirmed = 'confirmed' if self.confirmed else 'unconfirmed'
        return u'%s (%s)'%(self.title,confirmed)
