# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2021-04-04 22:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0001_initial'),
    ]

    operations = [
        # Recreate Vote model to keep non-null constraint for ForeignKeys
        migrations.DeleteModel(
            name='Vote',
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('point', models.PositiveSmallIntegerField(default=0)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='elections.Candidate')),
                ('voter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='elections.Voter')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([('voter', 'candidate', 'point')]),
        ),
    ]
