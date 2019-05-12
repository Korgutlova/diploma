# Generated by Django 2.1.7 on 2019-05-08 18:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0049_competition_max_for_criteria'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClusterNumber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.IntegerField(blank=True, choices=[(1, 'Ручная оценка'), (2, 'Взвешенное суммирование')], default=1, null=True, verbose_name='Тип оценивания')),
                ('k_number', models.IntegerField(default=1)),
                ('criterion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criterion_ks', to='fls.Criterion')),
            ],
        ),
        migrations.AlterField(
            model_name='competition',
            name='max_for_criteria',
            field=models.IntegerField(default=10, verbose_name='Ограничение критериев'),
        ),
        migrations.AlterUniqueTogether(
            name='clusternumber',
            unique_together={('criterion', 'type', 'k_number')},
        ),
    ]