# Generated by Django 3.2.2 on 2021-06-08 00:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('room', '0007_room_image_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='image_url',
            field=models.URLField(default=''),
        ),
    ]
