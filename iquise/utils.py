import hashlib, zlib
import cPickle as pickle
import urllib
import string
import random

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.db import models
from django.core.mail import send_mail as django_send_mail
from django.contrib.auth.models import User

from website.models import IQUISE, Donor

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

def send_mail(subj, msg, recipient_list):
    if settings.DEBUG:
        for recipient in recipient_list:
            users = User.objects.filter(email__iexact=recipient)
            if not any(u.is_staff and u.is_active for u in users): # Requires at least 1 active staff with that email
                raise RuntimeError("Can't send to '%s'. Can only send_mail to active staff when debugging"%recipient)
    django_send_mail(subj, msg, settings.DEFAULT_FROM_EMAIL, recipient_list)