# Generated by Django 2.1.7 on 2019-04-26 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0030_auto_20190426_2127'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='value',
            field=models.FloatField(default=0),
        ),
    ]
