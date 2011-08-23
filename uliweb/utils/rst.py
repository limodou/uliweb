from docutils.core import publish_parts
from docutils import nodes
from docutils.parsers.rst import directives
import re
import threading

g_data = threading.local()
g_data.g_style = {}

class highlight_block(nodes.General, nodes.Text):pass

from docutils.writers.html4css1 import Writer, HTMLTranslator

class SimpleWrite(Writer):
    def __init__(self):
        Writer.__init__(self)
        self.translator_class = SimpleHTMLTranslator
        
class SimpleHTMLTranslator(HTMLTranslator):
    def visit_highlight_block(self, node):
        self.body.append(node.astext())
    
    def depart_highlight_block(self, node):
        pass

def r_space(m):
    return len(m.group()) * '&nbsp;'

re_space = re.compile(r'^[ ]+', re.MULTILINE)
def code(name, arguments, options, content, lineno,
          content_offset, block_text, state, state_machine):
    global g_data
    
    if len(arguments) > 0:
        lang = arguments[0]
    else:
        lang = ''
    style, text = highlight('\n'.join(content), lang)
    text = re_space.sub(r_space, text)
    g_data.g_style[lang] = style
    return [highlight_block(text)]

code.content = 1
code.arguments = (0, 1, 1)
directives.register_directive('code', code)

def to_html(text, level=1, part='html_body'):
    global g_data
    g_data.g_style = {}
    source = text
    parts = publish_parts(source, writer=SimpleWrite(), settings_overrides={'initial_header_level':level})
    if g_data.g_style:
        style = '<style>' + '\n'.join(g_data.g_style.values()) + '</style>'
    else:
        style = ''
    return  style + '\n' + parts[part]

def parts(text, level=1, part='html_body'):
    global g_data
    g_data.g_style = {}
    source = text
    parts = publish_parts(source, writer=SimpleWrite(), settings_overrides={'initial_header_level':level})
    if g_data.g_style:
        style = '<style>' + '\n'.join(g_data.g_style.values()) + '</style>'
    else:
        style = ''
    return  style + '\n' + parts[part], parts

def highlight(code, lang):
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer, PythonLexer
    from pygments.formatters import HtmlFormatter
    try:
        lexer = get_lexer_by_name(lang)
    except:
        try:
            lexer = guess_lexer(code)
            lang = lexer.aliases[0]
        except:
            lexer = PythonLexer()
            lang = 'python'
    lang = lang.replace('+', '_')
    return HtmlFormatter().get_style_defs('.highlight_'+lang), highlight(code, lexer, HtmlFormatter(cssclass='highlight_'+lang))