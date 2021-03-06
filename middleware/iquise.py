import re

from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.views import redirect_to_login

from django.core.urlresolvers import reverse

from website.models import TemporaryToken

def get_login_url():
    return reverse(settings.LOGIN_URL)

def get_exempts():
    exempts = [re.compile(get_login_url().lstrip('/'))]
    if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
        exempts += [re.compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]
    return exempts


class LoginRequiredMiddleware(AuthenticationMiddleware):
    """When settings.REQUIRE_AUTH is True:
    Middleware that requires a user to be authenticated to view any page other
    than reverse(LOGIN_URL_NAME). Exemptions to this requirement can optionally
    be specified in settings via a list of regular expressions in
    LOGIN_EXEMPT_URLS (which you can copy from your urls.py).
    
    Requires authentication middleware and template context processors to be
    loaded. You'll get an error if they aren't.
    """
    def process_view(self, request, *args, **kwargs):
        if not request.user.is_authenticated() and settings.REQUIRE_AUTH:
            path = request.path.lstrip('/')
            if not any(m.match(path) for m in get_exempts()):
                return redirect_to_login(request.path)

class LoginTokenMiddleware(AuthenticationMiddleware):
    """Use website.model.TemporaryToken and GET parameters to log a user in."""
    def process_view(self, request, *args, **kwargs):
        token_value = request.GET.get("_token", None)
        if not token_value:
            return
        try:
            token = TemporaryToken.objects.get(token=token_value)
        except TemporaryToken.DoesNotExist:
            return
        if token.is_valid():
            login(request, token.user)
            token.times_used += 1
            token.save()
            request.session.set_expiry(0) # Expires on web browser closing