# Generated by Django 3.2.9 on 2021-11-05 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0008_auto_20200115_1048'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=32)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
        ),
    ]