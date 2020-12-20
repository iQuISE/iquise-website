from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError

from website.models import Presentation

class PresentationForm(forms.ModelForm):
    class Meta:
        exclude = ()
        model = Presentation

    def clean(self):
        confirmed = self.cleaned_data.get('confirmed')
        events = self.cleaned_data.get('event')
        if confirmed and events.count() != 1:
            raise ValidationError('A confirmed event must have one and only one event selected!')
        # Should only be one confirmed presentation per event
        conflicts = []
        for event in events:
            if self.instance.id:  # Editing
                conflicts += event.presentation_set.filter(confirmed=True).exclude(id=self.instance.id)
            else:  # Creating
                conflicts += event.presentation_set.filter(confirmed=True)
        if conflicts:
            error_msg = 'There is already a confirmed talk for:<br/>'
            error_msg += '<br/>'.join(['<a href="%s">%s: %s</a>'%(reverse('website:presentation',args=[conflict.id]),
                                        conflict.event.first(),conflict.title) for conflict in conflicts])
            raise ValidationError(mark_safe(error_msg))
