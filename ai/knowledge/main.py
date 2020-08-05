from ai.models import Vocabulary, Language, SoundVocabulary, PartOfSpeech, DigitalVocabulary
from ai.classes.translator_pinyin import translate_by_string
from dataparser.apps import ExcelParser
import re

class KnowledgeCenter():

    dot_pattern = re.compile("[\u3002|\u002c|\u300a|\u3008]")
    vocabulary_map = {}
    sound_vocabulary_map = {}
    SoundVocabulary_LV_map = {
        'NONE': 1,
        'TW': 2,
        'EN': 3,
        'CN': 4,
    }

    def __init__(self):
        pass
    

    def check_dictionary(self):
        _vs = Vocabulary.objects.values_list('context', flat=True)
        _svs = SoundVocabulary.objects.values_list('pinyin', flat=True)

        _vs_set = set()
        _svs_set = set()
        have_duplicate = False

        for _vocabulary in _vs:
            if _vocabulary in _vs_set:
                print('double vocabulary: {}'.format(_vocabulary))
                have_duplicate = True
            _vs_set.update({_vocabulary})

        for _pinyin_vocabulary in _svs:
            if _pinyin_vocabulary in _svs_set:
                print('double pinyin vocabulary: {}'.format(_pinyin_vocabulary))
                have_duplicate = True
            _svs_set.update({_pinyin_vocabulary})

        if not have_duplicate:
            print('Check Successful.')



    def absorb_dictionary(self, file_path, language_code='TW'):
        if file_path:

            ep = ExcelParser(file=file_path)
            rows = ep.get_row_list(column=['字詞名', '釋義', '詞性'])

            self.upsert_into_dictionary(rows, language_code)
    
    
    def upsert_into_dictionary(self, row_data, language_code='TW'):
        lan_code = Language.objects.get(code=language_code)
        part_speechs = PartOfSpeech.objects.all()
        part_map = {}
        for ps in part_speechs:
            part_map[ps.code.upper()] = ps
        
        vocabularies = Vocabulary.objects.all()
        vocabulary_set = set()
        for v in vocabularies:
            vocabulary_set.update({str(v)})
        
        _type_lv = self.SoundVocabulary_LV_map.get(language_code, None)
        if _type_lv is None:
            _type_lv = self.SoundVocabulary_LV_map.get('NONE')

        # print('upsert_into_dictionary row_data: ', row_data)
        length_rows = len(row_data)
        i = 0

        sound_vocabularies = SoundVocabulary.objects.all()
        sv_map = {}

        # _too_many_dup = 0
        for instance in sound_vocabularies:
            sv_map[str(instance)] = instance
        

        for _ in row_data:
            i += 1
            word = _[0].strip()

            if i % 100 == 0:
                print('Upsert Vocabularies.. process: {:.2f} % '.format( i / length_rows * 100 ), end='\r')
            
            # length_word = len(word)
            # if length_word > 12:
            #     continue # strange length

            # if word[0] < '\u4e00' or word[-1] < '\u4e00':
                # continue # is not chinese word

            if word in vocabulary_set:
                # print('Duplicate word: ', word)
                # _too_many_dup += 1
                # if _too_many_dup > 10:
                #     print('Too Many Duplicate Words Then Stop Upserting.')
                #     return self
                continue # already in database
            # _too_many_dup = 0
            
            # insert
            meaning = _[1]
            if meaning:
                rex_search = re.search(self.dot_pattern, meaning)
                if rex_search:
                    pos = rex_search.start()
                    if pos > 0:
                        meaning = meaning[:pos]


            _v = Vocabulary(
                context=word,
                meaning=meaning,
                language=lan_code,
            )
            _v.save()

            speech_code = _[2]
            if speech_code:
                speech_codes = speech_code.split(',')
                for sc in speech_codes:
                    sc = sc.strip().upper()
                    code = part_map.get(sc, None)
                    if code:
                        _v.part.add(code)
            
            vocabulary_set.update({word})
            
            # sound

            # word_pinyin = translate_by_string(word)
            word_pinyin = translate_by_string(word, no_tone=True)
            
            sv_instance = sv_map.get(word_pinyin, None)
            if sv_instance:

                sv_vocabularies = sv_instance.vocabulary.all()
                _not_duplicate = True
                for sv_v in sv_vocabularies:
                    if str(sv_v) == word:
                        _not_duplicate = False
                        break
                
                if _not_duplicate:
                    sv_instance.vocabulary.add(_v)

            else:

                new_sv = SoundVocabulary(pinyin=word_pinyin, type=_type_lv)
                new_sv.save()
                new_sv.vocabulary.add(_v)
                sv_map[word_pinyin] = new_sv

        print('Upsert Vocabularies Successful. process: 100.00 %  ')

        return self
    

    def absorb_digital_dictionary(self, file_path):
        if file_path:

            ep = ExcelParser(file=file_path)
            rows = ep.get_row_list(column=['數字', '翻譯'])

            self.upsert_into_digital_dictionary(rows)


    def upsert_into_digital_dictionary(self, row_data):

        _v_rows = [[_[1], '', ''] for _ in row_data]

        self.upsert_into_dictionary(_v_rows)

        digital_vocabularies = list(DigitalVocabulary.objects.values_list('pinyin', flat=True))

        length_rows = len(row_data)
        i = 0
        for _ in row_data:
            i += 1
            _digit = str(_[0]).strip()
            _digit = _digit.split('.')[0]
            _word = _[1]
            _word_pinyin = translate_by_string(_word)

            if i % 100 == 0:
                print('Upsert Digital Vocabularies.. process: {:.2f} % '.format( i / length_rows * 100 ), end='\r')

            if _word_pinyin in digital_vocabularies:
                continue

            _v = DigitalVocabulary(
                digits=_digit,
                pinyin=_word_pinyin,
            )
            _v.save()
            digital_vocabularies.append(_word_pinyin)

        
            
        print('Upsert Digital Vocabularies Successful. process: 100.00 %  ')

        return self
        
        