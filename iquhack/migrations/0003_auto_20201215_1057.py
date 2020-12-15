# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-12-15 15:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import iquhack.models


class Migration(migrations.Migration):

    dependencies = [
        ('iquhack', '0002_auto_20201213_0920_squashed_0003_auto_20201213_0946'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sponsorship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.BooleanField(default=False, help_text='This sponsor is also providing hardware/platform.')),
                ('agreement', models.FileField(blank=True, upload_to=iquhack.models.upload_sponsor_agreement)),
            ],
        ),
        migrations.AlterField(
            model_name='hackathon',
            name='back_drop_image',
            field=models.ImageField(help_text='A high-res progressive jpeg is the best option.', upload_to=iquhack.models.upload_backdrop),
        ),
        migrations.AlterField(
            model_name='sponsor',
            name='name',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='sponsor',
            unique_together=set([]),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='hackathon',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='iquhack.Hackathon'),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='sponsor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='iquhack.Sponsor'),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='tier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='iquhack.Tier'),
        ),
        migrations.RemoveField(
            model_name='sponsor',
            name='agreement',
        ),
        migrations.RemoveField(
            model_name='sponsor',
            name='hackathon',
        ),
        migrations.RemoveField(
            model_name='sponsor',
            name='platform',
        ),
        migrations.RemoveField(
            model_name='sponsor',
            name='tier',
        ),
        migrations.AddField(
            model_name='hackathon',
            name='sponsors',
            field=models.ManyToManyField(through='iquhack.Sponsorship', to='iquhack.Sponsor'),
        ),
        migrations.AlterUniqueTogether(
            name='sponsorship',
            unique_together=set([('hackathon', 'sponsor')]),
        ),
    ]
