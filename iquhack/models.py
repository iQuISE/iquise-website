from __future__ import unicode_literals

from django.db import models
from django.core.exceptions import ValidationError
import os

def upload_backdrop(instance, filename):
    """Upload backdrop using hackathon startdate as filename."""
    datestr = instance.start_date.isoformat()
    path = os.path.join("hackathon", datestr)
    ext = os.path.splitext(filename)[1] # .png, .jpg, etc.
    name = "banner_backdrop" + ext
    return os.path.join(path, name)

def upload_sponsor(instance, filename):
    """Upload sponsor based on sponsor name and year."""
    datestr = instance.hackathon.start_date.isoformat()
    path = os.path.join("hackathon", datestr)
    ext = os.path.splitext(filename)[1] # .pdf
    name = "agreement_" + instance.name.replace(" ", "_") + ext
    return os.path.join(path, name)

class Hackathon(models.Model):
    start_date = models.DateField(unique=True)
    end_date = models.DateField()
    back_drop_image = models.ImageField(upload_to=upload_backdrop)
    registration_link = models.URLField(blank=True, max_length=200)
    registration_deadline = models.DateTimeField()
    registration_open = models.BooleanField(default=False)
    registration_note = models.CharField(max_length=200)
    published = models.BooleanField(default=False, help_text="Make available on website.")
    logo_max_height = models.PositiveSmallIntegerField(default=50, help_text="In pixels.")

    def clean(self, *args, **kwargs):
        if self.end_date < self.start_date:
            raise ValidationError({"end_date": "Hackathon cannot end before it starts."})
        super(Hackathon, self).clean(*args,**kwargs)

    def save(self,*args,**kwargs):
        self.full_clean()
        super(Hackathon, self).save(*args,**kwargs)

    def __unicode__(self):
        return self.start_date.isoformat()

class Tier(models.Model):
    index = models.PositiveSmallIntegerField(default=0, unique=True, help_text="Higher numbers get rendered lower on page.")
    logo_rel_height = models.FloatField(default=100, help_text="Percentage")
    html_class = models.CharField(max_length=20, blank=True, help_text="Additional classes to add to the 'a' element of logo in html.")

    def __unicode__(self):
        return "Tier %i (%i%%)" % (self.index, round(self.logo_rel_height))

class CompanyContact(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50, unique=True)
    position = models.CharField(max_length=50, blank=True)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.email)

class Sponsor(models.Model):
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE)
    tier = models.ForeignKey(Tier, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to=upload_backdrop, blank=True, help_text="SVG files strongly encouraged!")
    company_contact = models.ForeignKey(CompanyContact, on_delete=models.SET_NULL, null=True)
    agreement = models.FileField(upload_to=upload_sponsor, blank=True)

    class Meta:
        unique_together = ("hackathon", "name")

    def __unicode__(self):
        return "%s (Tier %i)" % (self.name, self.tier.index)