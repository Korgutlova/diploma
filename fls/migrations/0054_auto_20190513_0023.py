# Generated by Django 2.1.7 on 2019-05-12 21:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fls', '0053_auto_20190512_1830'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(blank=True, choices=[(1, 'Новое'), (2, 'Отклоненное'), (3, 'Принятое')], default=1, null=True, verbose_name='Статус приглашения')),
                ('competition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competition_invitations', to='fls.Competition', verbose_name='Конкурс')),
                ('jury', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='jury_invitations', to='fls.CustomUser', verbose_name='Жюри')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='request',
            unique_together={('competition', 'participant')},
        ),
        migrations.AlterUniqueTogether(
            name='invitation',
            unique_together={('competition', 'jury')},
        ),
    ]
