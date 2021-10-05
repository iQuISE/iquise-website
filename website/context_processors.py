from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.urls import reverse

from website.models import IQUISE, Donor
from iquise.utils import encode_data

def basic_context(request):
    staff_reg_url = None
    if request.user.is_superuser:
        expires = (timezone.localtime()+timedelta(days=1)).strftime('%x%X')
        staff_reg_url = reverse('members:register',args=[''.join(encode_data(expires))])
    notifications = []
    if settings.DEBUG:
        notifications = ['DEVELOPMENT SERVER']
    extra_notification = request.session.pop("extra_notification", None)
    if extra_notification:
        notifications.append(extra_notification)
    # No analytics if superuser
    if request.user.is_superuser:
        useAnalytics = False
    else:
        useAnalytics = not settings.DEBUG
    iquise = IQUISE.objects.first() # Returns none if doesn't exist
    donors = [unicode(d) for d in Donor.objects.all()]
    return {'iquise':iquise,'useAnalytics': useAnalytics,'notifications':notifications,'donors':donors,'staff_reg_url':staff_reg_url}
