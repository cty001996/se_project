# Generated by Django 3.2.2 on 2021-06-01 01:53

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='created_time',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
