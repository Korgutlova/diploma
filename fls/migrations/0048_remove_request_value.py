# Generated by Django 2.1.7 on 2019-05-07 18:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0047_auto_20190507_2043'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='request',
            name='value',
        ),
    ]