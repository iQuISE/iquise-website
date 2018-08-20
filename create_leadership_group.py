import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iquise.settings")
django.setup()
from django.contrib.auth.models import User, Group, Permission

leadership, created = Group.objects.get_or_create(name='leadership')

permissions = ['add_logentry', 'change_logentry', 'delete_logentry', 'add_user',
               'change_user', 'delete_user', 'add_contenttype', 'change_contenttype',
               'delete_contenttype', 'add_session', 'change_session', 'delete_session']

if not created:
    # Previously found group.  Purging all permissions
    print 'Found existing "leadership" group, reseting permissions:'
    for p in leadership.permissions.all():
        print 'Removing:',p
        leadership.permissions.remove(p)

# All default app permissions
print ''
for p in Permission.objects.exclude(content_type__app_label='website'):
    if p.codename in permissions:
        print 'Adding:',p
        leadership.permissions.add(p)
# Add all website perms
for p in Permission.objects.filter(content_type__app_label='website'):
    if p.codename in ['add_profile','delete_profile']: continue
    print 'Adding:',p
    leadership.permissions.add(p)
# All meetings perms
for p in Permission.objects.filter(content_type__app_label='meetings'):
    print 'Adding:',p
    leadership.permissions.add(p)
leadership.save()
