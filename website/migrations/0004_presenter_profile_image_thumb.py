# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-09-01 01:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_auto_20180828_1558'),
    ]

    operations = [
        migrations.AddField(
            model_name='presenter',
            name='profile_image_thumb',
            field=models.ImageField(blank=True, editable=False, upload_to='presenters/thumbs'),
        ),
    ]
