import hashlib, zlib
import cPickle as pickle
import urllib
import string
import random

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from django.core.mail import send_mail as django_send_mail
from django.core.mail import mail_admins as django_mail_admins

def random_password():
    return ''.join([random.SystemRandom().choice(string.printable[0:95]) for i in range(15)])

def encode_data(data):
    """Turn `data` into a hash and an encoded string, suitable for use with `decode_data`."""
    text = zlib.compress(pickle.dumps(data, 0)).encode('base64').replace('\n', '')
    m = hashlib.md5(settings.SECRET_KEY + text).hexdigest()[:12]
    return m, text

def decode_data(hash_, enc):
    """The inverse of `encode_data`."""
    text = urllib.unquote(enc)
    m = hashlib.md5(settings.SECRET_KEY + text).hexdigest()[:12]
    if m != hash_:
        raise Exception("Bad hash!")
    data = pickle.loads(zlib.decompress(text.decode('base64')))
    return data

class AlwaysClean(models.Model):
    def save(self,*args,**kwargs):
        self.full_clean()
        super(AlwaysClean, self).save(*args,**kwargs)
    
    class Meta:
        abstract = True

ADMIN_EMAILS = [a[1] for a in settings.ADMINS]

def send_mail(subj, msg, recipient_list, user=None, **kwargs):
    if settings.DEBUG:
        if user and (user.is_active and user.is_staff and user.email):
            # If a staff is using, we will send an email to them but alter the body
            prefix = "<<DEBUGGING: This email would normally get sent to: %s>>\n" % (", ".join(recipient_list))
            msg = prefix + msg
            recipient_list = [user.email]
        else: # Otherwise the email must be that of an active staff (e.g. password resetting)
            for recipient in recipient_list:
                if recipient.lower() in ADMIN_EMAILS:
                    continue
                users = User.objects.filter(email__iexact=recipient)
                if not any(u.is_staff and u.is_active for u in users): # Requires at least 1 active staff with that email
                    raise RuntimeError("Can't send to '%s'. Can only send_mail to active staff when debugging"%recipient)
    django_send_mail(subj, msg, settings.SERVER_EMAIL, recipient_list, **kwargs)

def mail_admins(subj, msg, user=None, **kwargs):
    if settings.DEBUG: # We'll use the standard debugging logic in send_mail
        send_mail(subj, msg,  ADMIN_EMAILS, user=user, **kwargs)
    django_mail_admins(subj, msg, **kwargs)