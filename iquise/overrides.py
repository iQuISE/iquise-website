from django.contrib.auth import views as auth_views
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.models import User

from django.urls.base import reverse_lazy

class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    post_reset_login=True
    success_url=reverse_lazy('members:profile')

    def get(self, request, *args, **kw):
        """This will get called after validating token from self.dispatch.
        NOTE: This gets called _before_ the user actually updates their pasword, but
        has clearly proven they got the URL to do so.
        """
        if hasattr(self.user, "profile"):
            self.user.profile.email_confirmed = True
            self.user.profile.save()
        return super(PasswordResetConfirmView, self).get(request, *args, **kw)

class PasswordResetForm(auth_forms.PasswordResetForm):
    # This patches a Django<2.1 error where users who don't have passwords set
    # can't reset even if active
    def get_users(self, email):
        return User._default_manager.filter(**{
            '%s__iexact' % User.get_email_field_name(): email,
            'is_active': True,
        })
