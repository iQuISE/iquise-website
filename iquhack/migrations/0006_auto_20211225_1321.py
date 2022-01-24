# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2021-12-25 18:21
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import iquhack.models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('iquhack', '0005_auto_20211214_0904'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=60)),
                ('street', models.TextField()),
                ('postal_code', models.CharField(blank=True, max_length=12, verbose_name='ZIP or postal code')),
                ('country', models.CharField(max_length=60, verbose_name='Country or region')),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
            ],
        ),
        migrations.CreateModel(
            name='Guardian',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=60)),
                ('relationship', models.CharField(max_length=20)),
                ('email', models.EmailField(max_length=254)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('consent', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('github_username', models.CharField(help_text="The user name you use to login to <a href='https://github.com/'>GitHub</a>", max_length=64)),
                ('shipping_address', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='iquhack.Address')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='iquhack_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterModelOptions(
            name='faq',
            options={'ordering': ['usedfaq__index'], 'verbose_name': 'FAQ'},
        ),
        migrations.AddField(
            model_name='application',
            name='accepted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='hackathon',
            name='app_questions',
            field=iquhack.models.JSonField(default=b'[\n    {\n        "id": "participation_country",\n        "label": "What country do you plan to participate from?",\n        "type": "short"\n    },\n    {\n        "id": "under_18",\n        "label": "Are you under 18?",\n        "help_text": "If selected, we will require guardian contact information.",\n        "type": "radio",\n        "choices": [[true, "Yes"], [false, "No"]]\n    },\n    {\n        "id": "quant_comp",\n        "label": "Quantum Computation",\n        "type": "dropdown",\n        "choices": [[0, "None"], [1, "Some"], [2, "Expert"]]\n    },\n    {\n        "id": "experience",\n        "label": "Please select all the areas that you have had experience in",\n        "type": "multiple",\n        "choices": [\n            "Quantum Computation",\n            "Quantum Mechanics",\n            "Qiskit, Ocean, or any other quantum programming packages",\n            "Software design or engineering",\n            "Algorithms",\n            "Chemistry",\n            "Visual design",\n            "Basic programming"\n        ]\n    },\n    {\n        "id": "background_detail",\n        "label": "Please tell us a little more about your background",\n        "type": "long",\n        "max_length": 2000\n    },\n    {\n        "id": "interest_detail",\n        "label": "Why are you interested in participating in iQuHACK?",\n        "type": "long",\n        "max_length": 2000\n    },\n    {\n        "id": "how_heard",\n        "label": "How did you hear about iQuHACK?",\n        "type": "multiple",\n        "choices": [\n            "Website",\n            "Email",\n            "Facebook",\n            "Twitter",\n            "LinkedIn",\n            "News article",\n            "I participated last year"\n        ],\n        "required": false\n    }\n]', help_text='JSON encoded.'),
        ),
        migrations.AddField(
            model_name='guardian',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='iquhack.Profile'),
        ),
    ]