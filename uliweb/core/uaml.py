#! /usr/bin/env python
#coding=utf-8

import re
from StringIO import StringIO

COMMENT = 1
BEGIN_TAG = 2
CLOSE_TAG = 3
TAG = 4
VERBATIM = 5

# Tail end of ''' string.
Single3 = re.compile(r"[^'\\]*(?:(?:\\.|'(?!''))[^'\\]*)*'''")
# Tail end of """ string.
Double3 = re.compile(r'[^"\\]*(?:(?:\\.|"(?!""))[^"\\]*)*"""')
Triple = re.compile(r"'''" + '|' +  '"""')

TAG_WHITESPACE_ATTRS = re.compile('(\S+)([ \t]*?)')
CLASS_OR_ID = re.compile(r'([.#])((?:[^ \t\.#])+)')
TAG_AND_REST = re.compile(r'((?:[^ \t\.#])*)(.*)')
quotedText = r"""(?:(?:'(?:\\'|[^'])*')|(?:"(?:\\"|[^"])*"))"""
AUTO_QUOTE = re.compile("""^(\s+[^ \|\t=]+=)(""" + quotedText + """|[^ \|\t]+)|^(\s+[^ \|\t]+)""")
TEXT = re.compile(r'^\s*\| (.*)')
tabsize = 8

from uliweb.core.html import begin_tag, end_tag

class Writer(object):
    def unknown(self, indent, v):
        name, value, kwargs = v
        func_name = 'do_' + name
        if hasattr(self, func_name):
            return getattr(self, func_name)(indent, value, **kwargs)
        else:
            return indent*' ' + begin_tag(name, **kwargs) + value + end_tag(name)
    
    def unknown_begin(self, indent, v):
        name, value, kwargs = v
        func_name = 'begin_' + name
        if hasattr(self, func_name):
            return getattr(self, func_name)(indent, value, **kwargs)
        else:
            return indent*' ' + begin_tag(name, **kwargs)
    
    def unknown_close(self, indent, v):
        name, value, kwargs = v
        func_name = 'close_' + name
        if hasattr(self, func_name):
            return getattr(self, func_name)(indent)
        else:
            return indent*' ' + end_tag(name)
    
    def comment(self, indent, line):
        return indent*' ' + '<!-- %s -->' % line[2:]

    def verbatim(self, indent, value):
        return indent*' ' + value
    
handler_map = {
    COMMENT:'comment',
    VERBATIM:'verbatim',
    BEGIN_TAG:'unknown_begin',
    CLOSE_TAG:'unknown_close',
    TAG:'unknown',
}
class Parser(object):
    def __init__(self, text, writer=None):
        self.text = text
        self.writer = writer or Writer()
        self.result = []
        
    def run(self):
        result = []
        for token, indent, value in self.generate():
            func = getattr(self.writer, handler_map[token])
            result.append(func(indent, value))
          
        return '\n'.join(result)
    
    def __str__(self):
        return self.run()
        
    def generate(self):
        lnum = 0
        indents = [0]
        tags = ['']
        buf = []
        continued = False

        readline = StringIO(self.text).readline
        while 1:  
            line = readline()
            if not line: break
        
            line = line.rstrip()
            lnum = lnum + 1
            pos, max = 0, len(line)
            
            column = 0
            while pos < max:                   # measure leading whitespace
                if line[pos] == ' ': column = column + 1
                elif line[pos] == '\t': column = (column/tabsize + 1)*tabsize
                else: break
                pos = pos + 1
            
            if continued:
                if line[pos:].startswith('}}}'):
                    yield (VERBATIM, 0, '\n'.join(buf))
                    buf = []
                    continued = False
                else:
                    buf.append(line)
                continue
            
            if not line: continue
            
            #comment line
            if line[pos:].startswith('//'):
                yield (COMMENT, indents[-1], line[pos:])
                continue
            
            #{{{}}} block
            if line[pos:].startswith('{{{'):
                buf = []
                continued = True
                continue
              
            #| iteral line
            if line[pos:].startswith('|'):
                yield (VERBATIM, indents[-1], line[pos+1:])
                continue
            
            #process indent
            if column > indents[-1]:           # count indents or dedents
                indents.append(column)
                tag = tags[len(indents)-2]
                tags.append('')
                yield (BEGIN_TAG, indents[-2], tag)
                buf = []
                
            #process last buffer
            if buf and not continued:
                yield (TAG, indents[-1], buf[-1])
                buf = []
                
            #process dedent
            while column < indents[-1]:
                if column not in indents:
                    raise IndentationError(
                        "unindent does not match any outer indentation level",
                        ("<tokenize>", lnum, pos, line))
                tag = tags[len(indents)-2]
                indents = indents[:-1]
                tags = tags[:-1]
                yield (CLOSE_TAG, indents[-1], tag)
                buf = []
                
            #process tag_name
            t = TAG_WHITESPACE_ATTRS.search(line[pos:])
            tag = t.group(1)
            pos += t.end()
            
            t = TAG_AND_REST.match(tag)
            tag_name = t.group(1) or 'div'
            r = t.group(2)
            attr = {}
            for k, v in CLASS_OR_ID.findall(r):
                if k == '.':
                    if 'class' in attr:
                        attr['class'] += ' ' + v
                    else:
                        attr['class'] = v
                else:
                    attr['id'] = v
            value = ''
            
            #process tag_attr
            while 1:
                t = AUTO_QUOTE.search(line[pos:])
                if t:
                    v = t.groups()
                    pos += t.end()
                    if v[0] and v[1]:
                        name = v[0].strip()[:-1]
                        if v[1][0] in ('"\''):
                            _v = v[1][1:-1]
                        else:
                            _v = v[1]
                        
                        if name == 'class':
                            if 'class' in attr:
                                attr['class'] += ' ' + _v
                            else:
                                attr['class'] = _v
                        else:
                            attr[name] = _v
                    elif v[2]:
                        attr[v[2].strip()] = None
                else:
                    break
            #process tag_text
            t = TEXT.search(line[pos:])
            if t:
                value = t.group(1).strip()
            if value:
                yield (TAG, indents[-1], (tag_name, value, attr))
                buf = []
            else:
                tags[-1] = (tag_name, value, attr)
                buf.append((tag_name, value, attr))
            
        if buf:
            yield (TAG, indents[-1], buf[-1])
            
        #process dedent
        while len(tags) > 1:
            tag = tags[len(indents)-2]
            indents = indents[:-1]
            tags = tags[:-1]
            yield (CLOSE_TAG, indents[-1], tag)
        
            
if __name__ == '__main__':
#    print Parser(test).run()

    def test():
        text = """
{{{
<script>
var time;
</script>
}}}
form.form#form layout='table_line' color=red Test
    title | Input Something
    description | This is description
    panel
        .description.note class="good"
        //This is comment line
        field name="{{= field1}}" type=static
        field name=field2
        | {{Test}}
    line
        #tag
        p class=''
        field name=field3
        field name=field4
"""
        return Parser(text).run()
        
#    from timeit import Timer
#    t = Timer("test()", "from __main__ import test")
#    print t.timeit(1000)
    print test()