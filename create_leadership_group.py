import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iquise.settings")
django.setup()
from django.contrib.auth.models import User, Group, Permission

leadership, created = Group.objects.get_or_create(name='leadership')

permissions = ['add_logentry', 'change_logentry', 'delete_logentry', 'add_user',
               'change_user', 'delete_user', 'add_contenttype', 'change_contenttype',
               'delete_contenttype', 'add_session', 'change_session', 'delete_session',
               'add_iquise', 'change_iquise', 'delete_iquise', 'add_person',
               'change_person', 'delete_person', 'add_presentation', 'change_presentation',
               'delete_presentation', 'change_profile', 'add_school', 'change_school',
               'delete_school', 'add_department', 'change_department', 'delete_department']

if created:
    for perm in permissions:
        p = Permission.objects.get(codename=perm)
        print p
        leadership.permissions.add(p)
    leadership.save()
else:
    print 'Already exists, but not checking permissions, so no gurantee they are correct!'
