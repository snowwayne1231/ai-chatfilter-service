from django.contrib import admin
from service.models import Blockword, Whiteword

class BlockwordAdmin(admin.ModelAdmin):
    fields = ['text']
    list_display = ['text', 'date']
    empty_value_display = '---'

class WhitewordAdmin(admin.ModelAdmin):
    fields = ['text']
    list_display = ['text', 'date']
    empty_value_display = '---'
    

admin.site.register(Blockword, BlockwordAdmin)
admin.site.register(Whiteword, WhitewordAdmin)