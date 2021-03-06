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

def basic_context(request):
    staff_reg_url = None
    if request.user.is_superuser:
        expires = (timezone.localtime()+timedelta(days=1)).strftime('%x%X')
        staff_reg_url = reverse('members:register',args=[''.join(encode_data(expires))])
    notifications = []
    if settings.DEBUG:
        notifications = ['DEVELOPMENT SERVER']
    # No analytics if superuser
    if request.user.is_superuser:
        useAnalytics = False
    else:
        useAnalytics = not settings.DEBUG
    iquise = IQUISE.objects.first() # Returns none if doesn't exist
    donors = [unicode(d) for d in Donor.objects.all()]
    return {'iquise':iquise,'useAnalytics': useAnalytics,'notifications':notifications,'donors':donors,'staff_reg_url':staff_reg_url}

class AlwaysClean(models.Model):
    def save(self,*args,**kwargs):
        self.full_clean()
        super(AlwaysClean, self).save(*args,**kwargs)
    
    class Meta:
        abstract = True
