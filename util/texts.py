import re


def to_char(html):
    CHAR_ENTITIES = {'nbsp': ' ', '160': ' ',
                     'lt': '<', '60': '<',
                     'gt': '>', '62': '>',
                     'amp': '&', '38': '&',
                     'quot': '"', '34': '"', }

    re_charEntity = re.compile(r'&#?(?P<name>\w+);')
    sz = re_charEntity.search(html)
    while sz:
        entity = sz.group()  # entity全称，如&gt;
        key = sz.group('name')  # 去除&;后entity,如&gt;为gt
        try:
            html = re_charEntity.sub(CHAR_ENTITIES[key], html, 1)
            sz = re_charEntity.search(html)
        except KeyError:
            # 以空串代替
            html = re_charEntity.sub('', html, 1)
            sz = re_charEntity.search(html)
    return html


def to_text(html):
    re_cdata = re.compile('<!DOCTYPE HTML PUBLIC[^>]*>', re.I)
    re_script = re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', re.I)
    re_style = re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I)
    re_br = re.compile('<br\s*?/?>')
    re_h = re.compile('</?\w+[^>]*>')
    re_comment = re.compile('<!--[\s\S]*-->')
    re_font = re.compile('@@@.+?\:')
    s = re_cdata.sub('', html)
    s = re_script.sub('', s)
    s = re_style.sub('', s)
    s = re_br.sub('\n', s)
    s = re_h.sub(' ', s)
    s = re_comment.sub('', s)
    s = re_font.sub('', s)
    blank_line = re.compile('\n+')
    s = blank_line.sub('\n', s)
    s = to_char(s)
    s = re.sub('\s+', ' ', s)
    return s