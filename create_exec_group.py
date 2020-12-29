import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iquise.settings")
django.setup()
from django.contrib.auth.models import User, Group, Permission

execgroup, created = Group.objects.get_or_create(name='exec')

permissions = ['add_logentry', 'change_logentry', 'delete_logentry', 'add_user',
               'change_user', 'change_group', 'add_contenttype', 'change_contenttype',
               'delete_contenttype', 'add_session', 'change_session', 'delete_session']

if not created:
    # Previously found group.  Purging all permissions
    print 'Found existing "exec" group, reseting permissions:'
    for p in execgroup.permissions.all():
        print 'Removing:',p
        execgroup.permissions.remove(p)

# All default app permissions
print ''
for p in Permission.objects.exclude(content_type__app_label='website'):
    if p.codename in permissions:
        print 'Adding:',p
        execgroup.permissions.add(p)
# Add all website perms
for p in Permission.objects.filter(content_type__app_label='website'):
    if p.codename in ['add_profile','delete_profile']: continue
    print 'Adding:',p
    execgroup.permissions.add(p)
# All iquhack perms
for p in Permission.objects.filter(content_type__app_label='iquhack'):
    print 'Adding:',p
    execgroup.permissions.add(p)
# Members perms
permissions = ["add_position", "change_position"]
member_perms = Permission.objects.filter(content_type__app_label='members')
for perm in permissions:
    p = member_perms.get(codename=perm)
    print 'Adding:',p
    execgroup.permissions.add(p)
execgroup.save()
