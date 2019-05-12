# Generated by Django 2.1.7 on 2019-05-12 10:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0051_auto_20190511_1715'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='jurys',
            field=models.ManyToManyField(to='fls.CustomUser', verbose_name='Жюри конкурса'),
        ),
        migrations.AddField(
            model_name='competition',
            name='organizer',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='organizer_for_comp', to='fls.CustomUser', verbose_name='Оранизатор конкурса'),
            preserve_default=False,
        ),
    ]
