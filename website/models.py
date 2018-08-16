# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils import timezone

class EmailIField(models.EmailField):
    # Case-insensitive email field
    def clean(self,*args,**kwargs):
        value = super(EmailIField,self).clean(*args,**kwargs)
        return value.lower()

class IQUISE(models.Model):
    # Admin will limit this to a single entry
    description = models.TextField(max_length=2000)
    default_location = models.CharField(default='MIT Room 26-214',max_length=200)
    default_time = models.TimeField()

    class Meta:
        verbose_name = 'iQuISE'
        verbose_name_plural = u'\u200b'+u'iQuISE' # unicode invisible space to determine order (hack)

    def __unicode__(self):
        return u'iQuISE (%s)'%self.default_location

class School(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        verbose_name_plural = u'\u200b'*4+u'Schools' # unicode invisible space to determine order (hack)
    def __unicode__(self):
        return unicode(name)

class Department(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        verbose_name_plural = u'\u200b'*5+u'Departments' # unicode invisible space to determine order (hack)
    def __unicode__(self):
        return unicode(name.capitalize())

class Person(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    record_created = models.DateField(auto_now_add=True,blank=True)
    last_modified = models.DateField(auto_now=True,blank=True)
    # Rest are optional
    email = EmailIField(max_length=254,blank=True)
    MIT_ID = models.PositiveIntegerField(null=True,blank=True,verbose_name='MIT ID')
    year = models.CharField(max_length=10,blank=True,help_text='Sophomore, Graduate Year #, Postdoc, Professor, etc.')
    department = models.ForeignKey(Department, blank=True, null=True)
    school = models.ForeignKey(School, blank=True, null=True)
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
        qs = Person.objects.exclude(pk=self.pk).filter(email=self.email)
        if qs.exists():
            raise ValidationError(
                mark_safe('%s matches an existing user\'s email<br/>(contact <a href="mailto:iquise-leadership@mit.edu">iquise-leadership@mit.edu</a> for further assistance).'%self.email)
            )

    class Meta:
        verbose_name_plural = u'\u200b'*3+u'People' # unicode invisible space to determine order (hack)
    def __unicode__(self):
        return u'%s, %s'%(self.last_name.capitalize(),self.first_name.capitalize())

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
        dt = dt.replace(hour=iq[0].default_time.hour,minute=iq[0].default_time.minute,second=0,microseconds=0)
        return dt
    else:
        return None
class Presentation(models.Model):
    presenter = models.CharField(max_length=200)
    profile_image_url = models.URLField(max_length=200)
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=500)
    long_description = models.TextField(max_length=10000)
    description_url = models.URLField(max_length=200)
    supp_url = models.CharField('supplemental url',default=None, blank=True, max_length=200)
    affiliation = models.CharField(max_length=200)
    date = models.DateTimeField('presentation date',default=get_default_time)
    location = models.CharField(default=get_default_room,max_length=200)
    # Talk type
    THEORY = 'THEORY'
    EXPERIMENTAL = 'EXPERIMENT'
    TYPE_CHOICES = (
        (EXPERIMENTAL,'Experimental'),
        (THEORY,'Theoretical'),
    )
    type = models.CharField(max_length=20,choices=TYPE_CHOICES,default=EXPERIMENTAL)
    audience = models.ManyToManyField(Person,blank=True)

    class Meta:
        verbose_name_plural = u'\u200b'*2+u'Presentations' # unicode invisible space to determine order (hack)
        ordering = ['-date']
    def __unicode__(self):
        return unicode(self.title)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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
        instance.groups.add(Group.objects.get(name='leadership'))
# Save Profile when user created
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not instance.is_superuser:
        instance.profile.save()
