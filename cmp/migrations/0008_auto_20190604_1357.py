# Generated by Django 2.1.7 on 2019-06-04 10:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cmp', '0007_weights_ga'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GroupWeights',
        ),
        migrations.DeleteModel(
            name='Weights',
        ),
    ]
