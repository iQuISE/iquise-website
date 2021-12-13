from django import forms
from django.forms.fields import EmailField
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth.models import User

from .models import EmailList, ValidEmailDomain, Profile, SUBSCRIPTION_DISCLAIMER

def this_year():
    return timezone.now().year

LEVELS = ("Highschool", "Undergraduate", "Graduate", "PostDoc", "Professor", "Professional", "Retired")

class ValidateSubsMixin:
    SUBSCRIPTION_KEY = "subscriptions"
    new_domain = False

    def clean(self):
        cleaned_email = self.cleaned_data.get("email")
        if not cleaned_email: # Must have failed earlier
            return self.cleaned_data
        self.cleaned_data["email"] = cleaned_email = cleaned_email.lower()
        if User.objects.filter(email__iexact=cleaned_email).first(): # User already exists
            # TODO link to password reset?
            raise ValidationError({
                "email": "A user with this email already exists, email us for help."
            })
        # Now subscriptions (no earlier validation; assume key exists)
        # TODO: some stuff will differ here between ProfileForm and JoinForm
        if self.cleaned_data[self.SUBSCRIPTION_KEY].exists():
            domain = ValidEmailDomain.get_domain(cleaned_email)
            if domain and not domain.is_valid: # Definitely not allowed
                raise ValidationError({
                    self.SUBSCRIPTION_KEY: "Must use a university address to subscribe."
                })
            elif not domain: # Never seen domain
                self.new_domain = True
        return self.cleaned_data

class ProfileForm(forms.ModelForm):
    # TODO: Inherit ValidateSubsMixin
    first_name = forms.CharField()
    last_name = forms.CharField()
    # TODO: need to figure out behavior for subscription requests vs unsubscribe
    # Maybe temporarily link to unsubscribe from mailman and just present subs_request
    class Meta:
        model = Profile
        exclude = (
            "user", "profile_image", "email_confirmed", "year", "email",
            "further_info_url", "linkedin_url", "facebook_url", "twitter_url",
            "subscriptions", "subscription_requests"
        )

    field_order = ("first_name", "last_name", )

    def __init__(self, *args, **kw):
        super(ProfileForm, self).__init__(*args, **kw)
        if not self.instance:
            raise ValueError("Must instantiate with Profile instance")
        self.initial.update({
            "first_name": self.instance.user.first_name,
            "last_name": self.instance.user.last_name,
        })

    def save(self, commit=True):
        profile = super(ProfileForm, self).save(commit)
        user_opts = ("first_name", "last_name")
        for opt in user_opts:
            if self.cleaned_data.get(opt):
                setattr(profile.user, opt, self.cleaned_data.get(opt))
        if commit:
            self.instance.user.save()
        return profile

    def send_emails(self, request):
        if self.new_domain:
            ValidEmailDomain.new_domain_request(request.user, request)

class JoinForm(ValidateSubsMixin, UserCreationForm):
    """Join the iQuISE Community."""
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name") # We will use our own email field for username
    
    affiliation = forms.CharField(max_length=30, help_text="e.g. university, company")
    graduation_year = forms.IntegerField(initial=this_year, min_value=1900, help_text='Past, future or expected.')
    level = forms.ChoiceField(initial=Profile.LEVELS[1], choices=Profile.LEVELS)

    subscriptions = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple,
        queryset=EmailList.objects.all(),
        required=False,
        initial=[EmailList.objects.get(address="iquise-associates@mit.edu")],
        help_text=(
            "Your email must be a university email to join these lists. "
        ) + SUBSCRIPTION_DISCLAIMER
    )
    field_order = (
        "email", "first_name", "last_name", "affiliation", "graduation_year",
        "level", "subscriptions", "password1", "password2",
    )

    def __init__(self, *args, **kwargs):
        super(JoinForm, self).__init__(*args, **kwargs)
        for f in ("email", "first_name", "last_name"):
            self.fields[f].required = True
        self.fields["email"].widget.attrs.update({'autofocus': True})

    def save(self): # There is no commit=False here due to profile
        u = super(JoinForm, self).save(commit=False)
        u.username = u.email # TODO: Move to clean_username method
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
        username = self.cleaned_data.get('email')
        if username:
            username = username.lower()
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise ValidationError("Please enter a correct email and password.", code='invalid_login')
            elif not self.user_cache.is_active:
                raise ValidationError("This account is inactive.", code='inactive')

        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache