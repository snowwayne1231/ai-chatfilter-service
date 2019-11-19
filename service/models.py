from django.db import models



class Blockword(models.Model):
    text = models.CharField(max_length=64)
    date = models.DateTimeField(auto_now_add=True, blank=True)


class Whiteword(models.Model):
    text = models.CharField(max_length=64)
    date = models.DateTimeField(auto_now_add=True, blank=True)