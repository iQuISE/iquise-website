from django.contrib.auth.tokens import PasswordResetTokenGenerator

class EmailConfirmToken(PasswordResetTokenGenerator):
    """Exclude last_login timestamp since that shouldn't invalidate it."""
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.is_active)

email_confirmation_token = EmailConfirmToken()
