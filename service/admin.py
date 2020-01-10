from django.contrib import admin
from service.models import Blockword, Whiteword, BlockUser, BlockedSentence, GoodSentence, AnalyzingData

class BlockwordAdmin(admin.ModelAdmin):
    fields = ['text']
    list_display = ['text', 'date']
    empty_value_display = '---'

class WhitewordAdmin(admin.ModelAdmin):
    fields = ['text']
    list_display = ['text', 'date']
    empty_value_display = '---'

class BlockUserAdmin(admin.ModelAdmin):
    fields = ['name']
    list_display = ['name', 'date']
    empty_value_display = '---'

class BlockedSentenceAdmin(admin.ModelAdmin):
    fields = ['message', 'text', 'reason', 'type', 'status']
    list_display = ['message', 'text', 'reason', 'type', 'status', 'date']
    empty_value_display = '---'

class GoodSentenceAdmin(admin.ModelAdmin):
    fields = ['message', 'text', 'type', 'status']
    list_display = ['message', 'text', 'type', 'status', 'date']
    empty_value_display = '---'

class AnalyzingDataAdmin(admin.ModelAdmin):
    fields = ['year', 'month', 'day', 'good_sentence', 'blocked_sentence', 'json_blocked_detail', 'json_addition']
    list_display = ['year', 'month', 'day', 'good_sentence', 'blocked_sentence']
    empty_value_display = '---'
    

admin.site.register(Blockword, BlockwordAdmin)
admin.site.register(BlockUser, BlockUserAdmin)
admin.site.register(Whiteword, WhitewordAdmin)
admin.site.register(BlockedSentence, BlockedSentenceAdmin)
admin.site.register(GoodSentence, GoodSentenceAdmin)
admin.site.register(AnalyzingData, AnalyzingDataAdmin)
