# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2022-01-25 02:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iquhack', '0010_auto_20220124_2106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='mask_size',
            field=models.CharField(choices=[['0', 'YS/M'], ['1', 'YL/XL'], ['2', 'S/M'], ['3', 'L/XL'], ['4', 'N/A']], default='2', help_text="<a href='https://drive.google.com/file/d/1SiGfo68-teoHFz0xOZAi05rRRfkSOqIR/view?usp=sharing' target='_blank'>Sizing Chart</a>", max_length=1),
        ),
        migrations.AlterField(
            model_name='profile',
            name='shirt_size',
            field=models.CharField(choices=[['0', 'XS'], ['1', 'S'], ['2', 'M'], ['3', 'L'], ['4', 'XL'], ['5', 'XXL'], ['6', 'XXXL'], ['7', 'N/A']], default='2', max_length=1),
        ),
    ]
