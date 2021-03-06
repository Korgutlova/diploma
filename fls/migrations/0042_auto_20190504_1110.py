# Generated by Django 2.1.7 on 2019-05-04 08:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0041_auto_20190503_2201'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requestestimation',
            name='rank',
        ),
        migrations.AddField(
            model_name='requestestimation',
            name='criterion',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='criterion_avg_estimations', to='fls.Criterion'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='requestestimation',
            name='request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='request_avg_estimations', to='fls.Request'),
        ),
        migrations.AlterField(
            model_name='requestestimation',
            name='type',
            field=models.IntegerField(choices=[(1, 'Ручная оценка'), (2, 'Взвешенное суммирование')], default=1, verbose_name='Тип оценивания'),
        ),
    ]
