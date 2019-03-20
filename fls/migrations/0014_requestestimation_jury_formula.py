# Generated by Django 2.1.7 on 2019-03-19 20:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0013_auto_20190319_2305'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestestimation',
            name='jury_formula',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='formula_request_values', to='fls.CalcEstimationJury'),
        ),
    ]