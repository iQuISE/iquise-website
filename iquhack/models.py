from __future__ import unicode_literals
import os

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

def get_hackathon_path(hackathon):
    datestr = hackathon.start_date.isoformat()
    return os.path.join("hackathon", datestr)

def upload_backdrop(instance, filename):
    """Upload backdrop using hackathon startdate as filename."""
    path = get_hackathon_path(instance)
    ext = os.path.splitext(filename)[1] # .png, .jpg, etc.
    name = "banner_backdrop" + ext
    return os.path.join(path, name)

def upload_sponsor_logo(instance, filename):
    """Upload sponsor based on sponsor name and year."""
    path = get_hackathon_path(instance.hackathon)
    ext = os.path.splitext(filename)[1] # .svg
    name = instance.name.replace(" ", "_") + ext
    return os.path.join(path, name)

def upload_sponsor_agreement(instance, filename):
    """Upload sponsor based on sponsor name and year."""
    path = get_hackathon_path(instance.hackathon)
    ext = os.path.splitext(filename)[1] # .pdf
    name = "agreement_" + instance.name.replace(" ", "_") + ext
    return os.path.join(path, name)

# Currently allowing link to be blank for convenience, however this is quite dangerous!
# There is currently no reasonable error that occurs if no link is around when reg opens.
class Hackathon(models.Model):
    start_date = models.DateField(unique=True)
    end_date = models.DateField()
    back_drop_image = models.ImageField(upload_to=upload_backdrop)
    published = models.BooleanField(default=False, help_text="Make available on website.")
    # Registration stuff
    link = models.URLField(blank=True, max_length=200)
    early_note = models.CharField(max_length=200, blank=True)
    opens = models.DateTimeField()
    open_note = models.CharField(max_length=200, blank=True)
    deadline = models.DateTimeField(help_text="THIS WILL NOT PREVENT RESPONSES! Simply removes the link.")
    closed_note = models.CharField(max_length=200, blank=True)
    # Used for sponsor logos
    logo_max_height = models.PositiveSmallIntegerField(default=50, help_text="In pixels.")

    @property
    def early(self):
        return self.opens > timezone.now()

    @property
    def open(self):
        now = timezone.now()
        return self.opens <= now and now < self.deadline

    def clean(self, *args, **kwargs):
        if self.end_date < self.start_date:
            raise ValidationError({"end_date": "Hackathon cannot end before it starts."})
        if self.deadline <= self.opens:
            raise ValidationError({"deadline": "Registration cannot end before it opens."})
        super(Hackathon, self).clean(*args,**kwargs)

    def save(self,*args,**kwargs):
        self.full_clean()
        super(Hackathon, self).save(*args,**kwargs)

    def __unicode__(self):
        return self.start_date.isoformat() # yyyy-mm-dd

class Tier(models.Model):
    index = models.PositiveSmallIntegerField(default=0, unique=True, help_text="Higher numbers get rendered lower on page.")
    logo_rel_height = models.FloatField(default=100, help_text="Percentage. A value resulting in < 1 pixel won't be rendered.")
    side_margin = models.FloatField(default=12, help_text="Pixels.")
    bottom_margin = models.FloatField(default=8, help_text="Pixels.")

    def __unicode__(self):
        return "Tier %i (%i%%)" % (self.index, round(self.logo_rel_height))

# We could consider using a many-to-many field in Hackathon instead. We would then
# want to use a through model to capture tier, agreement, and contact. This would be
# particularly useful if we have the same sponsors each year; we could reuse their
# logo and name. Makes it also easier to do analytics in the future of which years
# a company supported iquhack.
class Sponsor(models.Model):
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE)
    tier = models.ForeignKey(Tier, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to=upload_sponsor_logo, blank=True, help_text="SVG files strongly encouraged!")
    link = models.URLField(blank=True, max_length=200)
    agreement = models.FileField(upload_to=upload_sponsor_agreement, blank=True)

    class Meta:
        unique_together = ("hackathon", "name")

    def __unicode__(self):
        return "%s (Tier %i)" % (self.name, self.tier.index)