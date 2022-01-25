from __future__ import unicode_literals
import os
import PIL
import json
from io import BytesIO
from easyaudit.models import CRUDEvent

from phonenumber_field.modelfields import PhoneNumberField

from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType

from iquise.utils import AlwaysClean
from members.models import get_term_containing

try:
    with open(os.path.join(os.path.dirname(__file__), "app_questions.json"), "r") as fid:
        DEFAULT_QS = fid.read()
except:
    DEFAULT_QS = ""

# TODO: FAQ and Section "general" currently not used to filter options in admin
# TODO: Add markdown processor for content too
CONTEXT_RENDER_HELP = (
            "This must be HTML! "
            "You can use the Django template language.<br>"
            "The following context will be available:<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;hackathon: The Hackathon database object.<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;formatted_event_date: The event's date formatted like 'February 1st-2nd'<br>"
        )

def convert_to_progressive_jpeg(image_field):
    """Swap an image_field content in memory before hitting file system.
    
    TODO: Finish implementing this; currently not working
    """
    img = PIL.Image.open(BytesIO(image_field.read()))
    output = BytesIO() # New memory buffer
    try:
        img.save(output, "JPEG", quality=85, optimize=True, progressive=True)
    except IOError:
        PIL.ImageFile.MAXBLOCK = img.size[0] * img.size[1]
        img.save(output, "JPEG", quality=85, optimize=True, progressive=True)
    output.seek(0) # Move cursor back to beginning of file
    # Update image_field
    image_field.path = os.path.splitext(image_field.path)[0] + ".jpg"
    image_field.file = output
    image_field.image = img

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
    """Upload sponsor based on sponsor name and year.
    
    TODO:
        Consider requiring svg OR make sure we're dealing with a reasonable resolution.
        It would be silly to be waiting for the website to load because of insanely hi-res logos!
    """
    ext = os.path.splitext(filename)[1] # .svg
    name = "%s%s" % (instance.name.replace(" ", "_"), ext)
    return os.path.join("sponsor_logos", name)

def upload_sponsor_agreement(instance, filename):
    """Upload sponsor based on sponsor name and year."""
    path = get_hackathon_path(instance.hackathon)
    ext = os.path.splitext(filename)[1] # .pdf
    name = "agreement_" + instance.sponsor.name.replace(" ", "_") + ext
    return os.path.join(path, name)

def upload_section_attachment(instance, filename):
    """Upload sponsor based on sponsor name and year."""
    path = get_hackathon_path(instance.section.hackathon)
    return os.path.join(path, filename)

class JSonField(models.TextField):
    def validate(self, value, model_instance):
        try:
            json.loads(value)
        except ValueError as e:
            raise ValidationError(str(e))
        return super(JSonField, self).validate(value, model_instance)


# There is currently no reasonable error that occurs if no questions exist when reg opens.
class Hackathon(models.Model):
    start_date = models.DateField(unique=True)
    end_date = models.DateField()
    back_drop_image = models.ImageField(upload_to=upload_backdrop, help_text="A high-res progressive jpeg is the best option.")
    published = models.BooleanField(default=False, help_text="Make available on website.")
    sponsors = models.ManyToManyField("Sponsor", through="Sponsorship")
    FAQs = models.ManyToManyField("FAQ", through="UsedFAQ")
    organizing_committee = models.ForeignKey(Group, null=True)
    # Registration stuff
    app_questions = JSonField(default=DEFAULT_QS, help_text="JSON encoded.")
    link = models.URLField(blank=True, max_length=200, help_text="DEPRECATED")
    early_note = models.CharField(max_length=200, blank=True)
    opens = models.DateTimeField()
    open_note = models.CharField(max_length=200, blank=True)
    deadline = models.DateTimeField()
    closed_note = models.CharField(max_length=200, blank=True)
    # Used for sponsor logos
    logo_max_height = models.PositiveSmallIntegerField(default=50, help_text="In pixels.")
    logo_max_side_margin = models.PositiveSmallIntegerField(default=12, help_text="In pixels.")
    logo_max_bottom_margin = models.PositiveSmallIntegerField(default=8, help_text="In pixels.")

    @property
    def early(self):
        return self.opens > timezone.now()

    @property
    def open(self):
        now = timezone.now()
        return self.opens <= now and now < self.deadline
    
    @property
    def finished(self):
        return self.end_date < timezone.now().date()

    @property
    def parsed_app_questions(self):
        return json.loads(self.app_questions)

    def get_organizers(self):
        if not self.organizing_committee:
            return []
        term = get_term_containing(self.start_date)
        if not term:
            return []
        return self.organizing_committee.committee.get_positions_held(term)

    def get_apps(self, accepted=False):
        return Application.objects.filter(hackathon=self, accepted=accepted)

    def get_parsed_apps(self):
        """Return a list of all applications and unique IDs.
        
        The first 2 columns returned are:
        1. datetime app was created (isoformat)
        2. user id

        The header is the q_ids. An asterisk represents a response that no longer
        is represented in the hackathon questions (probably edited after opened).
        """
        # TODO should be able to grab this CRUDevent datetime in one query; also
        # confirm that user and hackathon are fetched
        app_ct = ContentType.objects.get_for_model(Application)
        qs = self.parsed_app_questions
        header = ["Started", "User ID", "Email", "Email Confirmed"] + [q["id"] for q in qs]
        q_col = {q["id"]: header.index(q["id"]) for q in qs}
        rows = []
        for app in self.get_apps():
            responses = app.parsed_responses
            create_event = CRUDEvent.objects.get(event_type=CRUDEvent.CREATE, content_type=app_ct, object_id=app.id)
            row = [
                create_event.datetime,
                app.user.id,
                app.user.email,
                app.user.profile.email_confirmed,
            ] + [""] * len(responses)
            for q_id, r in responses.items():
                if q_id not in q_col:
                    header.append(q_id + "*")
                    q_col[q_id] = len(header)-1
                if isinstance(r, list):
                    row[q_col[q_id]] = ", ".join(r)
                else:
                    row[q_col[q_id]] = r
            rows.append(row)
        return header, rows

    def get_parsed_participants(self):
        """Return a list of all participant profiles and unique IDs."""
        # TODO: Mainly for shipping (plus email); generalize later
        header = ["User ID", "Phone", "Name", "Email", "Address1", "Address2", "City", "State", "Zip", "Country", "Size"]
        rows = []
        for app in self.get_apps(accepted=True):
            user = app.user
            addr = user.iquhack_profile.shipping_address or Address()
            streets= addr.street.splitlines()
            rows.append([
                user.id,
                addr.phone,
                user.get_full_name(),
                user.email,
                streets[0],
                "\n".join(streets[1:]), # \n join just in case!
                addr.city,
                addr.state,
                addr.postal_code,
                addr.country,
                app.parsed_responses.get("shirt_size"), # TODO Very temporary
            ])
        return header, rows

    def is_participant(self, user):
        if hasattr(user, "iquhack_apps") and hasattr(user, "iquhack_profile"):
            return user.iquhack_profile.all_consent and user.iquhack_apps.filter(hackathon=self, accepted=True).exists()
        return False

    def clean(self, *args, **kwargs):
        if self.end_date < self.start_date:
            raise ValidationError({"end_date": "Hackathon cannot end before it starts."})
        if self.deadline <= self.opens:
            raise ValidationError({"deadline": "Registration cannot end before it opens."})
        #convert_to_progressive_jpeg(self.back_drop_image)
        super(Hackathon, self).clean(*args,**kwargs)

    def __unicode__(self):
        return self.start_date.isoformat() # yyyy-mm-dd

    class Meta:
        ordering = ["-start_date"]

class Tier(AlwaysClean):
    index = models.PositiveSmallIntegerField(default=0, unique=True, help_text="Higher numbers get rendered lower on page.")
    logo_rel_size = models.FloatField(default=100, help_text="Percentage. A value resulting in < 1 pixel won't be rendered.")

    def __unicode__(self):
        return "Tier %i" % self.index

    class Meta:
        ordering = ["index"]

class Sponsor(AlwaysClean):
    name = models.CharField(max_length=50, unique=True)
    logo = models.FileField(upload_to=upload_sponsor_logo, blank=True, help_text="SVG files strongly encouraged!")
    link = models.URLField(blank=True, max_length=200)

    def __unicode__(self):
        if self.logo:
            return self.name
        else:
            return "%s (no logo!)" %self.name

class Sponsorship(AlwaysClean):
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE)
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE)
    tier = models.ForeignKey(Tier, on_delete=models.SET_NULL, null=True, blank=True)
    platform = models.BooleanField(default=False, help_text="This sponsor is also providing hardware/platform.")
    agreement = models.FileField(upload_to=upload_sponsor_agreement, blank=True)

    @property
    def have_agreement(self):
        return bool(self.agreement)

    def clean(self, *args, **kwargs):
        if not (self.platform or self.tier):
            raise ValidationError({"tier": "If not a platform sponsor, a tier needs to be specified."})
        super(Sponsorship, self).clean(*args,**kwargs)

    class Meta:
        unique_together = ("hackathon", "sponsor")
        ordering = ["-platform", "tier"] # Platform first, then ranked lowest first

class FAQ(AlwaysClean):
    question = models.CharField(max_length=100)
    answer = models.TextField(max_length=1000, help_text=CONTEXT_RENDER_HELP)
    general = models.BooleanField(default=False, help_text=(
        "Check this if this question and answer pair are general enough for any hackathon. "
        "If unchecked, it won't be listed in the hackathon's list of available FAQs."
    ))

    class Meta:
        verbose_name = "FAQ"
        ordering = ["usedfaq__index"]

    def __unicode__(self):
        return self.question

# TODO: consider hiding explicit index, and use orderable UI: https://djangosnippets.org/snippets/1053/
class UsedFAQ(AlwaysClean):
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE)
    FAQ = models.ForeignKey(FAQ, on_delete=models.CASCADE)
    index = models.PositiveSmallIntegerField(default=0, help_text="Higher numbers get rendered lower on page.")
    
    class Meta:
        verbose_name = "Used FAQ"
        unique_together = (("hackathon", "FAQ"), ("hackathon", "index"))
        ordering = ["index"]

# TODO: consider hiding explicit index, and use orderable UI: https://djangosnippets.org/snippets/1053/

class Section(AlwaysClean):
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE)
    index = models.PositiveSmallIntegerField(default=0, help_text="Higher numbers get rendered lower on page.")
    title = models.CharField(max_length=20)
    content = models.TextField(
        blank=True,
        help_text=(
            "%s<br><br>Additionally, this can implement sections defined in the template if provided."
            "<br>Files can be accessed using {{ attachments |get_item:'[NAME]' }} (careful with spaces)."
        ) % CONTEXT_RENDER_HELP
    )
    restricted = models.BooleanField(default=False, help_text="Only display to staff and accepted/consented participants while hackathon is running.")
    template = models.ForeignKey("SectionTemplate", on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = (("hackathon", "index"), ("hackathon", "title"))
        ordering = ["index"]

    def __unicode__(self):
        return "%s (%s)" % (self.title, self.hackathon)

class SectionTemplate(AlwaysClean):
    name = models.CharField(max_length=20, unique=True)
    content = models.TextField(help_text=CONTEXT_RENDER_HELP)

    def __unicode__(self):
        return self.name

class Attachment(AlwaysClean):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, help_text="If empty, will use filename without the extension.")
    file = models.FileField(upload_to=upload_section_attachment)

    def clean(self, *args, **kwargs):
        if not self.name:
            self.name = os.path.splitext(os.path.basename(self.file.path))[0]
        super(Attachment, self).clean(*args,**kwargs)

    class Meta:
        unique_together = ("section", "name")

    def __unicode__(self):
        return self.name

class Application(models.Model):
    class Meta:
        ordering = ['hackathon', '-accepted']

    """It is up to the form to perform any required validation."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="iquhack_apps", editable=False)
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE, editable=False)
    responses = JSonField(default="{}", help_text="JSON encoded.")
    accepted = models.BooleanField(default=False)

    @property
    def parsed_responses(self):
        return json.loads(self.responses)

    def accept(self, commit=True):
        """Accept this application and ensure a profile exists for user."""
        self.accepted = True
        if commit:
            self.save()
        if not hasattr(self.user, "iquhack_profile"):
            shirt_size = self.parsed_responses.get("shirt_size") # TODO: Hack for 2022
            Profile.objects.create(user=self.user, shirt_size=shirt_size)

    def __unicode__(self):
        return unicode(self.user)

class Address(models.Model):
    full_name = models.CharField(max_length=60)
    street = models.TextField() # Replaces address lines 1 and 2 in other forms
    postal_code = models.CharField(max_length=12, blank=True, verbose_name="ZIP or postal code")
    city = models.CharField(max_length=60)
    state = models.CharField(max_length=60, verbose_name="State/Province/Region", blank=True)
    country = models.CharField(max_length=60)
    phone = PhoneNumberField()

    # TODO: clean address

    def __unicode__(self):
        return self.full_name

class Profile(models.Model):
    user = models.OneToOneField(User, models.CASCADE, related_name="iquhack_profile")
    github_username = models.CharField(max_length=64, # github username max_length
        help_text=mark_safe("The user name you use to login to <a href='https://github.com/'>GitHub</a>")
    )
    shirt_size = models.CharField(default="2", max_length=1,
        choices=[["0", "XS"], ["1", "S"], ["2", "M"], ["3", "L"], ["4", "XL"], ["5", "XXL"], ["6", "XXXL"], ["7", "N/A"]]
    )
    mask_size = models.CharField(default="2", max_length=1,
        choices=[["0", "YS/M"], ["1", "YL/XL"], ["2", "S/M"], ["3", "L/XL"], ["4", "N/A"]], 
        help_text=mark_safe("<a href='https://drive.google.com/file/d/1SiGfo68-teoHFz0xOZAi05rRRfkSOqIR/view?usp=sharing' target='_blank'>Sizing Chart</a>")
    )
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, null=True, blank=True,
        help_text="We use this to ship you your swag."
    )
    pick_up = models.BooleanField(default=False, help_text="You can pick up your swag instead of us shipping it.")

    consent = models.BooleanField(default=False)

    # TODO: clean github username (if github reachable, use API query)

    @property
    def all_consent(self):
        return self.consent and self.guardian_set.all().count() == self.guardian_set.filter(consent=True).count()

    @property
    def complete(self):
        return self.github_username != "" and self.shipping_address is not None

    def __unicode__(self):
        return unicode(self.user)

class Guardian(models.Model):
    profile = models.ForeignKey(Profile, models.CASCADE)

    full_name = models.CharField(max_length=60)
    relationship = models.CharField(max_length=20)
    email = models.EmailField()
    phone = PhoneNumberField()
    consent = models.BooleanField(default=False)

    def __unicode__(self):
        return self.full_name
