from django.db import models

# Create your models here.

class CustomDictionaryWord(models.Model):
    text = models.CharField(max_length=32)
    date = models.DateTimeField(auto_now_add=True, blank=True)
