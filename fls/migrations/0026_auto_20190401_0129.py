# Generated by Django 2.1.7 on 2019-03-31 22:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0025_auto_20190401_0120'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subparam',
            name='type',
            field=models.IntegerField(choices=[(1, 'NUMBER'), (2, 'TEXT'), (3, 'FILE'), (4, 'PHOTO'), (5, 'ENUM'), (6, 'LINK')], default=1, verbose_name='Тип данных'),
        ),
    ]
