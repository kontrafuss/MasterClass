# Generated by Django 2.1.1 on 2019-12-31 02:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0005_auto_20191231_0214'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='subject',
        ),
        migrations.AddField(
            model_name='event',
            name='label',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.DeleteModel(
            name='Subject',
        ),
    ]
