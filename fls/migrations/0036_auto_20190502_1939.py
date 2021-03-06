# Generated by Django 2.1.7 on 2019-05-02 16:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0035_auto_20190502_1922'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParamValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField(blank=True, default=0, null=True)),
                ('text', models.TextField(blank=True, null=True)),
                ('enum_val', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cur_value_enum_values', to='fls.ValuesForEnum')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='subparamvalue',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='subparamvalue',
            name='enum_val',
        ),
        migrations.RemoveField(
            model_name='subparamvalue',
            name='request',
        ),
        migrations.RemoveField(
            model_name='subparamvalue',
            name='subparam',
        ),
        migrations.AlterField(
            model_name='uploaddata',
            name='sub_param_value',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='fls.ParamValue'),
        ),
        migrations.RenameModel(
            old_name='SubParam',
            new_name='Param',
        ),
        migrations.DeleteModel(
            name='SubParamValue',
        ),
        migrations.AddField(
            model_name='paramvalue',
            name='param',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='param_values', to='fls.Param'),
        ),
        migrations.AddField(
            model_name='paramvalue',
            name='request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='request_param_values', to='fls.Request'),
        ),
        migrations.AlterUniqueTogether(
            name='paramvalue',
            unique_together={('param', 'request')},
        ),
    ]
