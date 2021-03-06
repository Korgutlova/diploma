# Generated by Django 2.1.7 on 2019-03-07 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0003_auto_20190301_2320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competition',
            name='description',
            field=models.TextField(verbose_name='Описание конкурса'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='year_of_study',
            field=models.IntegerField(blank=True, choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '1(магистратура)'), (6, '2(магистратура)')], default=1, null=True, verbose_name='Курс'),
        ),
    ]
