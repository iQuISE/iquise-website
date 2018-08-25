from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *

class PersonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
    class Meta:
        model=Person
        fields = ('first_name','last_name','email','year','lab')

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30,required=True)
    last_name = forms.CharField(max_length=30,required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
        return user

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
            conflicts += event.presentation_set.filter(confirmed=True)
        if conflicts:
            error_msg = 'There is already a confirmed talk for:<br/>'
            error_msg += '<br/>'.join(['<a href="%s">%s: %s</a>'%(reverse('website:presentation',args=[conflict.id]),
                                        conflict.event.first(),conflict.title) for conflict in conflicts])
            raise ValidationError(mark_safe(error_msg))
