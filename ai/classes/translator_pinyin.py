from pypinyin import pinyin, Style

g_strict = False
g_heteronym = True

def translate_by_string(_string):
    _words = pinyin(_string, strict=g_strict, style=Style.NORMAL, heteronym=g_heteronym)

    _words = [_w[0] for _w in _words]

    _next = '_'.join(_words)

    return _next