# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django.db.models.signals import post_save


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
        return u'%s, %s'%(self.last_name.capitalize(),self.first_name.capitalize())

# User extention (staff)
class Profile(models.Model):
    # This is for the staff users only
    user = models.OneToOneField(User, models.CASCADE)
    role = models.CharField(max_length=200,blank=True)
    school_status = models.CharField(max_length=200,blank=True)
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
