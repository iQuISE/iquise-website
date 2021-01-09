# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2021-01-05 01:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import functools
import members.models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0010_auto_20210103_1548'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='term',
            options={'ordering': ['-start']},
        ),
        migrations.RemoveField(
            model_name='term',
            name='stop',
        ),
        migrations.AlterField(
            model_name='committee',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='auth.Group'),
        ),
        migrations.AlterField(
            model_name='term',
            name='start',
            field=models.DateField(default=functools.partial(members.models.get_current_term_start, *(), **{b'days': 365}), help_text="This term will extend to the next term's start date."),
        ),
    ]