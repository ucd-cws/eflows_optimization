# Generated by Django 2.2.4 on 2019-09-19 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('belleflopt', '0011_auto_20190919_1625'),
    ]

    operations = [
        migrations.AlterField(
            model_name='segmentcomponent',
            name='duration',
            field=models.PositiveSmallIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='segmentcomponent',
            name='start_day',
            field=models.PositiveSmallIntegerField(null=True),
        ),
    ]
