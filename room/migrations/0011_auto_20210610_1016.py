# Generated by Django 3.2.2 on 2021-06-10 02:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('room', '0010_auto_20210610_1007'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='roomblock',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='roominviting',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='roominvitingrequest',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='roommember',
            unique_together=set(),
        ),
    ]
