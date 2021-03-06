from ai.models import Vocabulary, SoundVocabulary, DigitalVocabulary, Language



def get_all_vocabulary_from_models(pinyin=True, english=True):

    _pinyins = []
    _englishs = []

    if english:
        lan_en = Language.objects.filter(code='EN').first()

        for v in Vocabulary.objects.filter(language=lan_en):
            _text = v.context
            _freq = v.freq
            _englishs.append([_text, _freq])
    
    # cdw_list = CustomDictionaryWord.objects.all()
    # for cdw in cdw_list:
    #     _cdw_pinyin = cdw.pinyin
    #     _freq = cdw.freq
    #     _pinyins.append([_cdw_pinyin, _freq])

    if pinyin:

        # if _i % 500 == 0:
        #     _percent = _i / _total * 100
        #     print(' {:.2f}%'.format(_percent), end="\r")
        # _i += 1

        sound_vocabularies = SoundVocabulary.objects.filter(status=1)

        for sv in sound_vocabularies:
            _pinyin = sv.pinyin
            _freq = sv.freq
            _pinyins.append([_pinyin, _freq])


        digital_vocabularies = DigitalVocabulary.objects.all()
        for dv in digital_vocabularies:
            digit = '{}_'.format(dv.digits)
            dv_pinyin = dv.pinyin
            _freq = 5
            _pinyins.append([digit, _freq])
            _pinyins.append([dv_pinyin, _freq])


    return {
        'pinyin': _pinyins,
        'english': _englishs,
    }