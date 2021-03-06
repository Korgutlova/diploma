# Generated by Django 2.1.7 on 2019-05-07 17:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0046_remove_competition_type_comp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customenum',
            name='competition',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='competition_enums', to='fls.Competition'),
        ),
        migrations.AlterField(
            model_name='valuesforenum',
            name='enum',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='values_for_enum', to='fls.CustomEnum', verbose_name='Перечисление'),
        ),
    ]
