from django.db import models


class AbstractMeaning(models.Model):
    meaning = models.CharField(max_length=1024)

    def __str__(self):
        return self.meaning


class Language(models.Model):
    code = models.CharField(max_length=8)
    chinese = models.CharField(max_length=8)

    def __str__(self):
        return self.code


class PartOfSpeech(models.Model):
    code = models.CharField(max_length=8)
    chinese = models.CharField(max_length=16)

    def __str__(self):
        return self.code


class Vocabulary(models.Model):
    context = models.CharField(max_length=255)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)
    status = models.IntegerField(default=1)
    is_common = models.BooleanField(default=True)
    meaning = models.CharField(max_length=512, blank=True, default="") 
    part = models.ManyToManyField(PartOfSpeech)
    abstract = models.ManyToManyField(AbstractMeaning)
    similarity = models.ManyToManyField("self")
    date = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['language',]),
            models.Index(fields=['status',]),
        ]

    def __str__(self):
        return self.context


class SoundVocabulary(models.Model):
    pinyin = models.CharField(max_length=65)
    type = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    vocabulary = models.ManyToManyField(Vocabulary)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'pinyin',]),
        ]

    def __str__(self):
        return self.pinyin


class DigitalVocabulary(models.Model):
    digits = models.CharField(max_length=65)
    pinyin = models.CharField(max_length=65, default='')
    type = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    vocabulary = models.ManyToManyField(Vocabulary)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'digits',]),
        ]

    def __str__(self):
        return self.digits

