# Generated by Django 2.2.4 on 2020-02-22 23:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('belleflopt', '0023_auto_20200222_1504'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='streamsegment',
            index=models.Index(fields=['com_id', 'name'], name='belleflopt__com_id_43c8fe_idx'),
        ),
        migrations.AddIndex(
            model_name='streamsegment',
            index=models.Index(fields=['com_id'], name='com_id_idx'),
        ),
        migrations.AddIndex(
            model_name='streamsegment',
            index=models.Index(fields=['downstream'], name='belleflopt__downstr_c30b7c_idx'),
        ),
    ]
