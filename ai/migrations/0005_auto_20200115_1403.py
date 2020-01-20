# Generated by Django 2.2.6 on 2020-01-15 06:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0004_auto_20200114_1648'),
    ]

    operations = [
        migrations.CreateModel(
            name='DigitalVocabulary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('digits', models.CharField(max_length=65)),
                ('type', models.IntegerField(default=1)),
                ('status', models.IntegerField(default=1)),
            ],
        ),
        migrations.RemoveIndex(
            model_name='soundvocabulary',
            name='ai_soundvoc_pinyin_75cdb9_idx',
        ),
        migrations.AddIndex(
            model_name='soundvocabulary',
            index=models.Index(fields=['status', 'pinyin'], name='ai_soundvoc_status_4ea150_idx'),
        ),
        migrations.AddField(
            model_name='digitalvocabulary',
            name='vocabulary',
            field=models.ManyToManyField(to='ai.Vocabulary'),
        ),
        migrations.AddIndex(
            model_name='digitalvocabulary',
            index=models.Index(fields=['status', 'digits'], name='ai_digitalv_status_05b869_idx'),
        ),
    ]