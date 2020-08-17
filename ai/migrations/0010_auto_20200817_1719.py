# Generated by Django 2.2.6 on 2020-08-17 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0009_newvocabulary_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='TextbookSentense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('origin', models.CharField(default='', max_length=512)),
                ('text', models.CharField(default='', max_length=255)),
                ('weight', models.IntegerField(default=1)),
                ('status', models.IntegerField(default=0)),
            ],
        ),
        migrations.AddIndex(
            model_name='textbooksentense',
            index=models.Index(fields=['status'], name='ai_textbook_status_890a96_idx'),
        ),
    ]
