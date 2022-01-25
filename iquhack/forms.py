import functools
from django import forms
import json
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.safestring import mark_safe

from .models import Application, Address, Guardian, Profile

APP_MAP = {
    "short": forms.CharField,
    "long": functools.partial(forms.CharField, widget=forms.Textarea),
    "radio": functools.partial(forms.ChoiceField, widget=forms.RadioSelect),
    "multiple": functools.partial(forms.MultipleChoiceField, widget=forms.CheckboxSelectMultiple),
    "dropdown": forms.ChoiceField,
}

class AppForm(forms.Form):
    def __init__(self, user, hackathon, *args, **kw):
        super(AppForm, self).__init__(*args, **kw)
        self.hackathon = hackathon
        self.user = user
        # Does the user have one for this hackathon already?
        # We could just set self.initial directly, but we'll do it this way in case
        # questions got added/removed
        self.instance = self.user.iquhack_apps.filter(hackathon=hackathon).first()
        initial = {}
        if self.instance:
            initial.update(self.instance.parsed_responses)
        # Prepare fields
        for q in hackathon.parsed_app_questions:
            q_label = q.get("label")
            if not q_label:
                raise ValueError("Question label not defined!")
            q_id = q.pop("id", q_label.replace(" ", "_"))
            typ_str = q.pop("type", "short")
            Typ = APP_MAP.get(typ_str)
            if not Typ:
                raise ValueError("Unknown field type '%s'.", typ_str)

            # We allow shorthand choices; update in-place
            if "choices" in q:
                for i, val in enumerate(q["choices"]):
                    if not isinstance(val, list): # Only possible to be list with json (no tuple, etc)
                        q["choices"][i] = [val, val]

            self.fields[q_id] = Typ(**q)
            init = initial.pop(q_id, None)
            if init:
                self.initial[q_id] = init
        # If we ever want to notify admins that questions changed we could do that here

    def save(self, commit=True):
        if not self.instance:
            self.instance = Application(user=self.user, hackathon=self.hackathon)
        self.instance.responses=json.dumps({q_id: self.cleaned_data[q_id] for q_id in self.fields})
        if commit:
            self.instance.save()
        return self.instance

class GuardianForm(forms.ModelForm):
    class Meta:
        model = Guardian
        exclude = ("profile", )
        widgets = {
            "consent": forms.CheckboxSelectMultiple(choices=[(True, "Received from guardian")])
        }
        help_texts = {
            "email": "We will use this address to request consent.",
            "consent": "After you save, we will send an email to the provided contact for consent."
        }
    
    def __init__(self, *args, **kw):
        super(GuardianForm, self).__init__(*args, **kw)
        self.fields["consent"].disabled = True
        if self.instance and self.instance.email:
            self.fields["email"].disabled = True
            self.fields["email"].help_text += " If you need to update it, please contact us."
        

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ("user", "shipping_address")
        widgets = {
            "consent": forms.CheckboxSelectMultiple(choices=[(True, "Yes")]),
            "mask_size": forms.RadioSelect,
            "pick_up": forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
        }
        labels = {
            "pick_up": "Will you be able to pick up your iQuHACK swag from MIT's campus?",
        }
        help_texts = { # TODO: temp for 2022 (don't hardcode link!)
            "consent": mark_safe("<a href='https://drive.google.com/file/d/1_X8uktXFMSj9qCa_SeFXIePdPYh5mHAo/view?usp=sharing' target='_blank'> Code of Conduct and Data Release </a>"),
            "pick_up": (
                "Please note that all participants located within the Greater Boston Area are required to pick up their Swag from MIT's campus. "
                "And, as a token of our appreciation in helping lower shipping fees, we may provide extra swag on a first-come first-serve basis. "
                "Please email iquhack@mit.edu with any additional inquiries regarding this."
            )
        }
    
    def __init__(self, *args, **kw):
        super(ProfileForm, self).__init__(*args, **kw)
        self.fields["consent"].required = True
        self.fields["shirt_size"].disabled = True

class AddrForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ()
        widgets = {
            "street": forms.Textarea(attrs={"rows":2,}),
        }

    def clean_street(self):
        street = self.cleaned_data["street"].strip()
        if len(street.splitlines()) > 2:
            raise ValidationError("Street can be 1 or 2 lines only.")
        return street

class BulkApprovalForm(forms.Form):
    user_ids = forms.CharField(widget=forms.Textarea,
        help_text="Enter user IDs using the same delimitter throughout."
    )

    def __init__(self, hackathon, *args, **kw):
        super(BulkApprovalForm, self).__init__(*args, **kw)
        self.hackathon = hackathon
    
    def clean_user_ids(self):
        user_ids = self.cleaned_data["user_ids"].strip()
        apps = []
        missing = []
        # Find delim
        delim = ""
        if not user_ids[0].isdigit():
            raise ValidationError("Unexpected first character. Make sure the values are integer user IDs.")
        for char in user_ids:
            if not char.isdigit():
                delim += char
            if delim and char.isdigit():
                break
        if delim:
            parsed_ids = user_ids.split(delim)
        else: # Must be single entry
            parsed_ids = [user_ids]
        for user_id in parsed_ids:
            user_id = user_id.strip()
            if not user_id: continue # Empty line we can ignore
            app = Application.objects.filter(hackathon=self.hackathon, user__id=user_id).first()
            if app:
                apps.append(app)
            else: # We go through all to build up a complete list for the error
                missing.append(user_id)
        if missing:
            raise ValidationError("%s user(s) do not have apps for this hackathon."%", ".join(missing))
        return apps

    def save(self):
        with transaction.atomic():
            for app in self.cleaned_data["user_ids"]:
                app.accept() # TODO: move to app model
