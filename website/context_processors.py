from django.conf import settings

from website.models import IQUISE, Donor

def basic_context(request):
    notifications = []
    if settings.DEBUG:
        notifications = ['DEVELOPMENT SERVER']
    extra_notification = request.session.pop("extra_notification", None)
    if extra_notification:
        notifications.append(extra_notification)
    # No analytics if superuser
    user = getattr(request, "user", None)
    useAnalytics = not settings.DEBUG
    if user and user.is_superuser:
        useAnalytics = False
    iquise = IQUISE.objects.first() # Returns none if doesn't exist
    donors = [unicode(d) for d in Donor.objects.all()]
    return {
        'iquise':iquise,
        'useAnalytics': useAnalytics,
        'notifications':notifications,
        'donors':donors,
    }
