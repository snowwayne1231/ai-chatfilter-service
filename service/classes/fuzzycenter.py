from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from datetime import datetime
from service.models import Blockword
from zhconv import convert

class FuzzyCenter():
    """
    """
    user_define_ratio = 80
    wording_define_ratio = 70
    temporary_text_list = []
    temporary_timereserve = 0

    block_words = []
    block_sentence = []
    


    def __init__(self):
        self.temporary_timereserve = 3 * 60 # 3 minitues
        self.refresh_block_words()
        

    
    def refresh_block_words(self):
        blockword_objects = Blockword.objects.all()
        block_words = []
        block_sentence = []
        for blockword in blockword_objects:
            
            _text = blockword.text
            _cn, _zh = self.parse_cnzh(_text)

            if len(_text) == 1:
                if not _text in block_words:
                    block_words.append(_text)
                    if _cn != _text:
                        block_words.append(_cn)
                    elif _zh != _text:
                        block_words.append(_zh)
            else:
                if not _text in block_sentence:
                    block_sentence.append(_text)
                    if _cn != _text:
                        block_sentence.append(_cn)
                    elif _zh != _text:
                        block_sentence.append(_zh)

        self.block_words = block_words
        self.block_sentence = block_sentence
        return self

    
    def parse_cnzh(self, txt):
        _cn = convert(txt, 'zh-cn')
        _zh = convert(txt, 'zh-tw')
        return _cn, _zh


    def upsert_temp_text(self, text, user, room, lv, anchor, prediction):
        _now = datetime.now()
        _timestamp = datetime.timestamp(_now)

        self.temporary_text_list = [_ for _ in self.temporary_text_list if (_[0] + self.temporary_timereserve) > _timestamp][:500]

        _loc = [_timestamp, text, user, room, lv, anchor, prediction]

        self.temporary_text_list.insert(0, _loc)

        # print(self.temporary_text_list)

        return self


    def get_temp_texts(self, user, room):
        return [_ for _ in self.temporary_text_list if fuzz.ratio(_[2], user) > self.user_define_ratio and _[3] == room and _[6] == 0]


    def get_merged_text(self, text, user, room):
        texts = self.get_temp_texts(user, room)
        if len(texts) == 0:
            return text

        lastest_text = texts[0]
        res_text = ''

        if len(text) < 5:
            has_general = False
            for _t in text:
                if _t <= u'\u007a':
                    has_general = True
                    break
            
            if has_general:
                res_text = lastest_text[1] + text
            else:
                return text
        else:        
            _now = datetime.now()
            _timestamp = datetime.timestamp(_now)
            if _timestamp - lastest_text[0] < 10:
                res_text = lastest_text[1] + text
            else:
                return text
        
        return res_text if len(res_text) > 0 else None


    def find_fuzzy_block_word(self, text, silence=False):
        block_words = self.block_words
        block_sentence = self.block_sentence
        # print('find_fuzzy_block_word')
        # print('text: ', text)
        
        
        text_length = len(text)
        if text_length == 0:
            pass
        elif text_length == 1:
            # one word ratio
            extract_word = process.extractOne(text, block_words, scorer=fuzz.ratio)
            word_possible = extract_word[1]
            word_txt = extract_word[0]

            if word_possible >= self.wording_define_ratio:
                return word_txt

        else:

            # have up two word as sentence
            extract_sentence = process.extractOne(text, block_sentence, scorer=fuzz.token_set_ratio)
            sentence_possible = extract_sentence[1]
            sentence_txt = extract_sentence[0]

            # print('extract_sentence: ', extract_sentence)

            if sentence_possible >= self.wording_define_ratio:
                return sentence_txt
            
            else:

                # same single dirty word
                for b_word in block_words:
                    if text.find(b_word) >= 0:
                        same_word_num = 0
                        for _ in text:
                            if b_word == _:
                                same_word_num += 1
                        
                        if (same_word_num / text_length) * 100 >= self.wording_define_ratio:
                            return b_word

                        break 
        
        return None

