# Generated by Django 2.2.6 on 2020-04-22 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0008_auto_20200131_1840'),
    ]

    operations = [
        migrations.AddField(
            model_name='newvocabulary',
            name='text',
            field=models.CharField(default='', max_length=65),
        ),
    ]
