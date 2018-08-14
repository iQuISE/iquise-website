# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver

class IQUISE(models.Model):
    # Admin will limit this to a single entry
    description = models.TextField(max_length=2000)
    default_location = models.CharField(default='MIT Room 26-214',max_length=200)

    class Meta:
        verbose_name_plural = 'iQuISE'

    def __unicode__(self):
        return u'iQuISE'

class Presentation(models.Model):
    presenter = models.CharField(max_length=200)
    profile_image_url = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=500)
    long_description = models.CharField(max_length=10000)
    description_url = models.CharField(max_length=200)
    supp_url = models.CharField(default=None, blank=True, max_length=200)
    affiliation = models.CharField(max_length=200)
    date = models.DateTimeField('presentation date')
    location = models.CharField(default='MIT Room 26-214',max_length=200)

    def __unicode__(self):
        return u'%s (%s)'%(self.title,self.presenter)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=200,blank=True)
    school_status = models.CharField(max_length=200,blank=True)
    profile_image_url = models.CharField(max_length=200,blank=True)
    further_info_url = models.CharField(blank=True, max_length=200)

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
