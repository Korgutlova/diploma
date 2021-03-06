# Generated by Django 2.1.7 on 2019-04-25 23:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0027_auto_20190420_0234'),
    ]

    operations = [
        migrations.AddField(
            model_name='criterion',
            name='param',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='criterion_params', to='fls.Param', verbose_name='Критерий определенного параметра'),
        ),
        migrations.AddField(
            model_name='criterion',
            name='result_formula',
            field=models.BooleanField(default=False),
        ),
    ]
