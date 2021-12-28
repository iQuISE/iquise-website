import functools
from django import forms
import json

from django.forms import inlineformset_factory
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
            "consent": forms.CheckboxSelectMultiple(choices=[(True, "Yes")])
        }
        help_texts = {
            "consent": mark_safe("<a href='https://drive.google.com/file/d/1_X8uktXFMSj9qCa_SeFXIePdPYh5mHAo/view?usp=sharing' target='_blank'> Code of Conduct and Data Release </a>"),
        }
    
    def __init__(self, *args, **kw):
        super(ProfileForm, self).__init__(*args, **kw)
        self.fields["consent"].required = True

class AddrForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ()
        widgets = {
            "street": forms.Textarea(attrs={"rows":2,}),
        }
