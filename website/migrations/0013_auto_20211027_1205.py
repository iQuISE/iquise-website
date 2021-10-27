# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2021-10-27 17:05
from __future__ import unicode_literals

from django.db import migrations

def forwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        if cursor.db.vendor == "sqlite": # sqlite (what we use for unit tests) can't do this
            return
        print('')
        print('    Altering database ...')
        cursor.execute("ALTER DATABASE CHARACTER SET utf8 COLLATE utf8_bin;")
        cursor.execute("SHOW TABLES;")
        for table, in cursor.fetchall():
            print('    Altering table %s ...' % table)
            cursor.execute(
                "ALTER TABLE %s CONVERT TO CHARACTER SET utf8 COLLATE utf8_bin" % table
            )

def backwards(self, orm):
    # Altering the tables takes lots of time and
    # locks the tables, since it copies all the data.
    raise RuntimeError(
        "This migration probably took 2 hours, you don't really want to rollback ..."
    )

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0012_temporarytoken'),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
