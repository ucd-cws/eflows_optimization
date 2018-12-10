# Generated by Django 2.1.4 on 2018-12-08 22:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FlowComponent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='HUC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('huc_id', models.CharField(max_length=13)),
                ('initial_available_water', models.IntegerField()),
                ('flow_allocation', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Species',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('common_name', models.CharField(max_length=255)),
                ('pisces_fid', models.CharField(max_length=6)),
            ],
        ),
        migrations.CreateModel(
            name='SpeciesComponents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('threshold', models.FloatField(default=0.8)),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='eflows.FlowComponent')),
                ('species', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='eflows.Species')),
            ],
        ),
        migrations.AddField(
            model_name='huc',
            name='assemblage',
            field=models.ManyToManyField(related_name='presence', to='eflows.Species'),
        ),
        migrations.AddField(
            model_name='huc',
            name='downstream',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='eflows.HUC'),
        ),
        migrations.AddField(
            model_name='huc',
            name='upstream',
            field=models.ManyToManyField(related_name='_huc_upstream_+', to='eflows.HUC'),
        ),
        migrations.AddField(
            model_name='flowcomponent',
            name='species',
            field=models.ManyToManyField(related_name='components', through='eflows.SpeciesComponents', to='eflows.Species'),
        ),
    ]
