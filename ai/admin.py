from django.contrib import admin
from ai.models import AbstractMeaning, Language, PartOfSpeech, Vocabulary, SoundVocabulary


class AbstractMeaningAdmin(admin.ModelAdmin):
    fields = ['meaning']
    list_display = ['meaning']
    empty_value_display = '---'


class LanguageAdmin(admin.ModelAdmin):
    fields = ['code', 'chinese']
    list_display = ['code', 'chinese']
    empty_value_display = '---'


class PartOfSpeechAdmin(admin.ModelAdmin):
    fields = ['code', 'chinese']
    list_display = ['code', 'chinese']
    empty_value_display = '---'


class VocabularyAdmin(admin.ModelAdmin):
    fields = ['context', 'language', 'status', 'meaning', 'part', 'abstract']
    list_display = ['context', 'status', 'meaning', 'date']
    readonly_fields = ('context',)
    sortable_by = ('date',)
    empty_value_display = '---'

    search_fields = ('context',)


class SoundVocabularyAdmin(admin.ModelAdmin):
    # fields = ['pinyin', 'type', 'status']
    fields = ['pinyin', 'type', 'status', 'vocabulary']
    list_display = ['pinyin', 'type', 'status']
    # list_editable = ['type', 'status']
    empty_value_display = '---'

    readonly_fields = ('vocabulary',)
    search_fields = ('pinyin',)

    


admin.site.register(AbstractMeaning, AbstractMeaningAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(PartOfSpeech, PartOfSpeechAdmin)
admin.site.register(Vocabulary, VocabularyAdmin)
admin.site.register(SoundVocabulary, SoundVocabularyAdmin)