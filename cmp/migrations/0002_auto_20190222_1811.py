# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-02-22 15:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cmp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weights',
            name='deviations_sum',
            field=models.FloatField(),
        ),
    ]
