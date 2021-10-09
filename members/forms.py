from django import forms
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from iquise.utils import mail_admins
from .models import EmailList, ValidEmailDomain

def this_year():
    return timezone.now().year

class JoinForm(forms.Form):
    """Join the iQuISE Community.
    
    This form implies a request to join iquise-associates@mit.edu.
    """
    LEVELS = ("Highschool", "Undergraduate", "Graduate", "PostDoc", "Professor", "Professional", "Retired")
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField(help_text='You must use your university email.')
    affiliation = forms.CharField(max_length=30, help_text="e.g. university, company")
    graduation_year = forms.IntegerField(initial=this_year, min_value=1900, help_text='Past, future or expected.')
    level = forms.ChoiceField(initial=LEVELS[1], choices=zip(LEVELS, LEVELS))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.represented = True
        super(JoinForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        cleaned_email = self.cleaned_data["email"].lower()
        if (User.objects.filter(email__iexact=cleaned_email).first() or 
            User.objects.filter(username=cleaned_email).first()):
            # User already exists
            raise ValidationError("A user with this email already exists, email iquise-exec@mit.edu for help.")
        valid, represented = ValidEmailDomain.check_email(cleaned_email)
        if not valid and represented: # Definitely not allowed
            raise ValidationError(
                "Not recognized as a university address. Email us if you think this is a mistake."
                )
        elif not represented: # Unknown
            self.represented = False
        return cleaned_email

    def save(self):
        with transaction.atomic():
            u = User.objects.create(
                username=self.cleaned_data["email"],
                email=self.cleaned_data["email"],
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data["last_name"],
            )
            u.profile.affiliation = self.cleaned_data["affiliation"]
            u.profile.graduation_year = self.cleaned_data["graduation_year"]
            u.profile.level = self.cleaned_data["level"]
            u.profile.subscription_requests.add(
                EmailList.objects.get(address="iquise-associates@mit.edu")
            )
            u.profile.save()
            if not self.represented:
                domain = self.cleaned_data["email"].split("@")[-1].lower()
                v, _ = ValidEmailDomain.objects.get_or_create(domain=domain, status="u")
                # Email admins for quick review
                msg = (
                    "A request to join the community was received from an unverified domain:\n"
                    "%s (profile: %s) \n\n"
                    "You should reply to this user directly if you choose to deny this request. "
                    "They have not been contacted yet.\n\n"
                    "You can add this domain to the database to avoid having to do this manual labor!\n%s"
                ) % (
                    self.cleaned_data["email"],
                    self.request.build_absolute_uri(reverse('admin:auth_user_change', args=[u.id])),
                    self.request.build_absolute_uri(reverse('admin:members_validemaildomain_change', args=[v.id])),
                )
                mail_admins("New Domain Request", msg, user=self.request.user)
        return u

class RegistrationForm(UserCreationForm):
    """This form is to register as an iQuiSE admin."""
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
