from django import forms
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from iquise.utils import random_password

def this_year():
    return timezone.now().year

class JoinForm(forms.Form):
    LEVELS = ("Highschool", "Undergraduate", "Graduate", "PostDoc", "Professor", "Professional", "Retired")
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField(help_text='Please use your university email if possible.')
    affiliation = forms.CharField(max_length=30)
    graduation_year = forms.IntegerField(initial=this_year, min_value=1900, help_text='Past, future or expected.')
    level = forms.ChoiceField(initial=LEVELS[1], choices=zip(LEVELS, LEVELS))

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def save(self):
        u = User.objects.create(
            username=self.cleaned_data["email"],
            email=self.cleaned_data["email"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            password=random_password(),
        )
        u.profile.affiliation = self.cleaned_data["affiliation"]
        u.profile.graduation_year = self.cleaned_data["graduation_year"]
        u.profile.level = self.cleaned_data["level"]
        u.profile.save()

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
