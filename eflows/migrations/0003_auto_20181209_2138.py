# Generated by Django 2.1.4 on 2018-12-10 05:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('eflows', '0002_auto_20181208_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='huc',
            name='downstream',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='upstream_single_huc', to='eflows.HUC'),
        ),
        migrations.AlterField(
            model_name='huc',
            name='flow_allocation',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='huc',
            name='initial_available_water',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='huc',
            name='upstream',
            field=models.ManyToManyField(related_name='upstream_relationship_dont_use', to='eflows.HUC'),
        ),
    ]
