from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six

class EmailConfirmToken(PasswordResetTokenGenerator):
    """Exclude last_login timestamp since that shouldn't invalidate it."""
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )

email_confirmation_token = EmailConfirmToken()