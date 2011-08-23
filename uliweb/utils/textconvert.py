#coding=utf-8
import re
import cgi

re_string = re.compile(r'(?P<htmlchars>[<&>])|(?P<space>^[ \t]+)|(?P<lineend>\r\n|\r|\n)|(?P<protocal>(^|\s*)(http|ftp|https)://[\w\-\.,@?^=%&amp;:/~\+#]+)', re.S|re.M|re.I)
def text2html(text, tabstop=4):
    def do_sub(m):
        c = m.groupdict()
        if c['htmlchars']:
            return cgi.escape(c['htmlchars'])
        if c['lineend']:
            return '<br/>'
        elif c['space']:
            t = m.group().replace('\t', '&nbsp;'*tabstop)
            t = t.replace(' ', '&nbsp;')
            return t
        else:
            url = m.group('protocal')
            if url.startswith(' '):
                prefix = ' '
                url = url[1:]
            else:
                prefix = ''
            return '%s<a href="%s">%s</a>' % (prefix, url, url)
    return re.sub(re_string, do_sub, text)

if __name__ == '__main__':
    text=("I like python!\r\n"
    "UliPad <<The Python Editor>>: http://code.google.com/p/ulipad/\r\n"
    "UliWeb <<simple web framework>>: http://uliwebproject.appspot.com\r\n"
    "My Blog: http://hi.baidu.com/limodou")
    print text2html(text)
    