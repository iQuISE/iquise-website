from django import forms
from django.forms.fields import EmailField
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth.models import User

from .models import EmailList, ValidEmailDomain, Profile

def this_year():
    return timezone.now().year

class JoinForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name") # We will use our own email field for username

    """Join the iQuISE Community."""
    LEVELS = ("Highschool", "Undergraduate", "Graduate", "PostDoc", "Professor", "Professional", "Retired")
    
    affiliation = forms.CharField(max_length=30, help_text="e.g. university, company")
    graduation_year = forms.IntegerField(initial=this_year, min_value=1900, help_text='Past, future or expected.')
    level = forms.ChoiceField(initial=LEVELS[1], choices=zip(LEVELS, LEVELS))

    subscriptions = forms.ModelMultipleChoiceField(
        queryset=EmailList.objects.all(),
        required=False,
        initial=[EmailList.objects.get(address="iquise-associates@mit.edu")],
        help_text=(
            "Your email must be a university email to join these lists. "
            "We do our best to update subscriptions weekly, but keep in mind we're a small volunteer team!"
        )
    )
    field_order = (
        "email", "first_name", "last_name", "affiliation", "graduation_year",
        "level", "subscriptions", "password1", "password2",
    )

    def __init__(self, *args, **kwargs):
        self.new_domain = False
        super(JoinForm, self).__init__(*args, **kwargs)
        for f in ("email", "first_name", "last_name"):
            self.fields[f].required = True
        self.fields["email"].widget.attrs.update({'autofocus': True})

    def clean_email(self):
        cleaned_email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=cleaned_email).first(): # User already exists
            # TODO link to password reset?
            raise ValidationError("A user with this email already exists, email us for help.")
        return cleaned_email

    def clean_subscriptions(self):
        if self.cleaned_data["subscriptions"].exists():
            valid, represented = ValidEmailDomain.check_email(
                self.cleaned_data.get("email", self.data.get("email", ""))
            )
            if represented and not valid: # Definitely not allowed
                raise ValidationError("Must use a university address to subscribe.")
            elif not represented: # Never seen domain
                self.new_domain = True
        return self.cleaned_data["subscriptions"]

    def save(self): # There is no commit=False here due to profile
        u = super(JoinForm, self).save(commit=False)
        u.username = u.email
        u.save() # This will create the profile

        u.profile.affiliation = self.cleaned_data["affiliation"]
        u.profile.graduation_year = self.cleaned_data["graduation_year"]
        u.profile.level = self.cleaned_data["level"]
        u.profile.subscription_requests.set(self.cleaned_data["subscriptions"])
        u.profile.save()
        return u

    def send_emails(self, user, request):
        Profile.send_email_confirmation(user, request)
        if self.new_domain:
            ValidEmailDomain.new_domain_request(user, request)


class LoginForm(forms.Form):
    email = EmailField(
        widget=forms.TextInput(attrs={'autofocus': True}),
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput,
    )

    def __init__(self, request=None, *args, **kwargs):
        # Basically a copy of from django.contrib.auth.forms.AuthenticationForm
        self.request = request
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('email').lower()
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise ValidationError( "Please enter a correct email and password.", code='invalid_login')
            elif not self.user_cache.is_active:
                raise ValidationError("This account is inactive.", code='inactive')

        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache