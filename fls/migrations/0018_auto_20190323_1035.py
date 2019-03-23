# Generated by Django 2.1.7 on 2019-03-23 07:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0017_competition_max_limit'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='status',
            field=models.IntegerField(blank=True, choices=[(1, 'Создание'), (2, 'Открыт'), (3, 'Оценивание'), (4, 'Закрыт')], default=1, null=True, verbose_name='Статус конкурса'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='method_of_estimate',
            field=models.IntegerField(blank=True, choices=[(1, 'Абсолютная оценка заявки'), (2, 'Попарное сравнение заявок'), (3, 'Попарные сравнения параметров'), (4, 'Ранжирование параметров'), (5, 'Автоматически')], default=1, null=True, verbose_name='Метод оценивания'),
        ),
        migrations.AlterField(
            model_name='estimationjury',
            name='type',
            field=models.IntegerField(blank=True, choices=[(1, 'Абсолютная оценка заявки'), (2, 'Попарное сравнение заявок'), (3, 'Попарные сравнения параметров'), (4, 'Ранжирование параметров')], default=1, null=True, verbose_name='Тип оценивания'),
        ),
        migrations.AlterField(
            model_name='requestestimation',
            name='type',
            field=models.IntegerField(choices=[(1, 'Абсолютная оценка заявки'), (2, 'Попарное сравнение заявок'), (3, 'Попарные сравнения параметров'), (4, 'Ранжирование параметров')], default=1, verbose_name='Тип оценивания'),
        ),
    ]
