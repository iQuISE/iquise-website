import functools
from django import forms
import json

from .models import Application, ApplicationQuestions

APP_MAP = {
    "short": forms.CharField,
    "long": functools.partial(forms.CharField, widget=forms.Textarea),
    "radio": functools.partial(forms.ChoiceField, widget=forms.RadioSelect),
    "multiple": functools.partial(forms.MultipleChoiceField, widget=forms.CheckboxSelectMultiple),
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
            initial.update(json.loads(self.instance.responses))
        # Prepare fields
        for q in json.loads(hackathon.app_questions.defs):
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
            init = initial.pop(q_id)
            if init:
                self.initial[q_id] = init
        # If we ever want to notify admins that questions changed we could do that here

    def save(self, commit=True):
        if not self.instance:
            self.instance = Application(user=self.user, hackathon=self.hackathon)
        # We always update questions and responses together to make sure we know what the user saw
        self.instance.questions = self.hackathon.app_questions.defs
        self.instance.responses=json.dumps({q_id: self.cleaned_data[q_id] for q_id in self.fields})
        if commit:
            self.instance.save()
        return self.instance