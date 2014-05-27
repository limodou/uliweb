#coding=utf8
from __future__ import print_function
import os
from uliweb.core.template import *
import time

path = os.path.dirname(__file__)
dirs = [os.path.join(path, 'templates')]

def test():
    """
    >>> d = {'myvalue':'XXX'}
    >>> print (template("<html>{{= myvalue }}</html>", d))
    <html>XXX</html>
    """

def test_auto_escape():
    """
    >>> d = {'v':'<span></span>'}
    >>> print (template("<html>{{= v }}</html>", d))
    <html>&lt;span&gt;&lt;/span&gt;</html>
    """

def test_escape():
    """
    >>> d = {'v':'<span></span>'}
    >>> print (template("<html>{{<< v }}</html>", d))
    <html><span></span></html>
    """

def test_embed():
    """
    >>> d = {'v':'<span></span>'}
    >>> print (template("<html>{{embed v }}</html>", d))
    <html><span></span></html>
    """

def test_single_comment():
    """
    >>> d = {'v':'<span></span>'}
    >>> txt = '''
    ... <html>{{<< v }}</html>
    ... {{# comment line}}'''
    >>> print (template(txt, d))
    <BLANKLINE>
    <html><span></span></html>
    <BLANKLINE>
    """

def test_multiple_comment():
    """
    >>> d = {'v':'<span></span>'}
    >>> txt = '''
    ... <html>{{<< v }}</html>
    ... {{## comment line
    ... {{v}}
    ... ##}}'''
    >>> print (template(txt, d))
    <BLANKLINE>
    <html><span></span></html>
    <BLANKLINE>
    """

def test_if():
    """
    >>> d = {'v':True}
    >>> txt = '''
    ... {{if v:}}ok{{pass}}
    ... '''
    >>> print (template(txt, d))
    <BLANKLINE>
    ok
    <BLANKLINE>
    """

def test_if_else():
    """
    >>> d = {'v':True}
    >>> txt = '''
    ... {{if v:}}ok{{else:}}no{{pass}}
    ... '''
    >>> print (template(txt, d))
    <BLANKLINE>
    ok
    <BLANKLINE>
    >>> print (template(txt, {'v':False}))
    <BLANKLINE>
    no
    <BLANKLINE>
    """

def test_if_elif_else():
    """
    >>> d = {'v':1}
    >>> txt = '''
    ... {{if v==1:}}1{{elif v==2:}}2{{else:}}other{{pass}}
    ... '''
    >>> print (template(txt, d))
    <BLANKLINE>
    1
    <BLANKLINE>
    >>> print (template(txt, {'v':2}))
    <BLANKLINE>
    2
    <BLANKLINE>
    >>> print (template(txt, {'v':3}))
    <BLANKLINE>
    other
    <BLANKLINE>
    """

def test_multi_if():
    """
    >>> d = {'a':True, 'b':False}
    >>> txt = '''
    ... {{if a:}}
    ... {{if b:}}ok{{else:}}no{{pass}}
    ... {{pass}}
    ... '''
    >>> print (template(txt, d))
    <BLANKLINE>
    <BLANKLINE>
    no
    <BLANKLINE>
    <BLANKLINE>
    """

def test_for():
    """
    >>> d = {'v':['a', 'b']}
    >>> txt = '''{{for i in v:}}
    ... {{=i}}
    ... {{pass}}'''
    >>> print (template(txt, d))
    <BLANKLINE>
    a
    <BLANKLINE>
    b
    <BLANKLINE>
    """

def test_for_break():
    """
    >>> d = {'v':['a', 'b']}
    >>> txt = '''{{for i in v:}}
    ... {{if i=='b':}}{{break}}{{pass}}
    ... {{=i}}
    ... {{pass}}'''
    >>> print (template(txt, d))
    <BLANKLINE>
    <BLANKLINE>
    a
    <BLANKLINE>
    <BLANKLINE>
    """

def test_for_continue():
    """
    >>> d = {'v':['a', 'b']}
    >>> txt = '''{{for i in v:}}
    ... {{if i=='b':}}{{continue}}{{pass}}
    ... {{=i}}
    ... {{pass}}'''
    >>> print (template(txt, d))
    <BLANKLINE>
    <BLANKLINE>
    a
    <BLANKLINE>
    <BLANKLINE>
    """

def test_while():
    """
    >>> d = {'v':['a', 'b']}
    >>> txt = '''{{i=0}}{{while i<2:}}
    ... {{=v[i]}}
    ... {{i+=1}}
    ... {{pass}}'''
    >>> print (template(txt, d))
    <BLANKLINE>
    a
    <BLANKLINE>
    <BLANKLINE>
    b
    <BLANKLINE>
    <BLANKLINE>
    """

def test_statment():
    """
    >>> d = {}
    >>> txt = '''{{a='abc'}}{{b='cde'}}
    ... {{import os}}
    ... {{= os.path.join(a, b)}}
    ... '''
    >>> print (template(txt, d))
    <BLANKLINE>
    <BLANKLINE>
    abc/cde
    <BLANKLINE>
    """

def test_multi_statements_1():
    """
    >>> d = {}
    >>> txt = '''{{a='abc'
    ... b='cde'
    ... import os}}
    ... {{= os.path.join(a, b)}}
    ... '''
    >>> print (template(txt, d))
    <BLANKLINE>
    abc/cde
    <BLANKLINE>
   """

def test_multi_statements_2():
    """
    >>> d = {}
    >>> txt = '''{{a=True
    ... if a:
    ...     b = 'ok'
    ... else:
    ...     b = 'no'
    ... pass}}
    ... {{= b}}
    ... '''
    >>> print (template(txt, d))
    <BLANKLINE>
    ok
    <BLANKLINE>
    """

def test_out_write():
    """
    >>> d = {}
    >>> txt = '''{{out.write('ok')}}'''
    >>> print (template(txt, d))
    ok
    """

def test_def():
    """
    >>> d = {}
    >>> txt = '''{{def t(x):}}
    ... {{out.write(x)}}
    ... {{pass}}
    ... {{t('ok')}}'''
    >>> print (template(txt, d))
    <BLANKLINE>
    <BLANKLINE>
    ok
    <BLANKLINE>
    """

def test_def_multiple_lines():
    """
    >>> d = {}
    >>> txt = '''{{def t(x):
    ...     out.write(x)
    ...     pass}}
    ... {{t('ok')}}'''
    >>> print (template(txt, d))
    <BLANKLINE>
    ok
    """

def test_begin_end_tags():
    """
    >>> d = {}
    >>> txt = '''{{BEGIN_TAG}}{{END_TAG}}'''
    >>> print (template(txt, d))
    {{}}
    """

def test_block():
    """
    >>> txt = '''<html>
    ... {{block title}}title{{end}}
    ... </html>'''
    >>> print (template(txt))
    <html>
    title
    </html>
    >>> txt = '''<html>
    ... {{block title}}title{{end title}}
    ... </html>'''
    >>> print (template(txt))
    <html>
    title
    </html>
    """

def test_nested_block():
    """
    >>> txt = '''<html>
    ... {{block title}}title{{block child}}child{{end}}{{end}}
    ... </html>'''
    >>> print (template(txt))
    <html>
    titlechild
    </html>
    """

def test_file():
    """
    >>> d = {'name':'uliweb'}
    >>> print (template_file('file.html', d, dirs=dirs))
    Hello, uliweb
    """

def test_extend():
    """
    >>> d = {'name':'uliweb'}
    >>> dirs = [os.path.join(path, 'templates', x) for x in ['a']]
    >>> print (template_file('index.html', d, dirs=dirs))
    <html>
    <head>
    <title>Untitled</title>
    </head>
    <body>
    <BLANKLINE>
    <h1>Hello, uliweb</h1>
    main1
    side1
    <BLANKLINE>
    </body>
    </html>
    """

def test_extend():
    """
    >>> d = {'name':'中文'}
    >>> dirs = [os.path.join(path, 'templates', x) for x in ['a']]
    >>> print (template_file('test_third.html', d, dirs=dirs))
    <html>
    <head>
    <title>Untitled</title>
    </head>
    <body>
    <BLANKLINE>
    <h1>Hello, 中文</h1>
    中文
    side1
    <BLANKLINE>
    </body>
    </html>
    """

def test_extend_self():
    """
    >>> d = {'name':'uliweb'}
    >>> dirs = [os.path.join(path, 'templates', x) for x in ['b', 'a']]
    >>> print (template_file('index.html', d, dirs=dirs))
    <html>
    <head>
    <title>title2</title>
    </head>
    <body>
    <BLANKLINE>
    main
    side
    <BLANKLINE>
    </body>
    </html>
    """

def test_customize_tag():
    """
    >>> d = {'name':'uliweb'}
    >>> dirs = [os.path.join(path, 'templates', x) for x in ['a']]
    >>> print (template_file('new_tag.html', d, dirs=dirs))
    <BLANKLINE>
    uliweb
    """

def test_include():
    """
    >>> d = {'name':'uliweb'}
    >>> dirs = [os.path.join(path, 'templates', x) for x in ['b', 'a']]
    >>> print (template_file('parent.html', d, dirs=dirs))
    <html>
    <head>
    <title>title2</title>
    </head>
    <body>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    uliweb
    <BLANKLINE>
    side
    <BLANKLINE>
    </body>
    </html>
    """

def test_error_1():
    """
    >>> d = {'v':'<span></span>'}
    >>> try:
    ...     print (template("<html>{{= v </html>", d))
    ... except ParseError as e:
    ...     print (e)
    Missing end expression }} on line 1
    """

def test_default_template():
    """
    >>> dirs = [os.path.join(path, 'templates', x) for x in ['b', 'a']]
    >>> loader = Loader(dirs)
    >>> loader.resolve_path('x.html', default_template='index.html') # doctest:+ELLIPSIS
    '.../index.html'
    >>> x = loader.load('x.html', default_template='index.html')
    """

def test_find_template():
    """
    >>> dirs = [os.path.join(path, 'templates', x) for x in ['b', 'a']]
    >>> loader = Loader(dirs)
    >>> loader.find_templates('index.html') # doctest:+ELLIPSIS
    ['.../b/index.html', '.../a/index.html']
    """

def test_print_tree_template():
    """
    >>> dirs = [os.path.join(path, 'templates', x) for x in ['b', 'a']]
    >>> loader = Loader(dirs)
    >>> loader.print_tree('parent.html') # doctest:+ELLIPSIS
    templates/b/parent.html
    <BLANKLINE>
    -------------- Tree --------------
         templates/a/layout.html
             (extend)templates/b/layout.html
    -----------> (extend)templates/b/parent.html
                     (include)templates/a/new_tag.html
    >>> loader.print_tree('index.html') # doctest:+ELLIPSIS
    templates/b/index.html
    <BLANKLINE>
    -------------- Tree --------------
         templates/a/layout.html
             (extend)templates/b/layout.html
    -----------> (extend)templates/b/index.html
    """

def test_lru():
    """
    >>> u = LRUTmplatesCacheDict(max_size=2)
    >>> dir = os.path.join(path, 'templates', 'b')
    >>> f1 = os.path.join(dir, 'layout.html')
    >>> f2 = os.path.join(dir, 'index.html')
    >>> f3 = os.path.join(dir, 'parent.html')
    >>> u[f1] = 'f1'
    >>> u[f2] = 'f2'
    >>> u[f3] = 'f3'
    >>> print (u.keys()) # doctest:+ELLIPSIS
    ['.../b/parent.html', '.../b/layout.html']
    """

def test_depends():
    """
    >>> dirs = [os.path.join(path, 'templates', x) for x in ['b', 'a']]
    >>> loader = Loader(dirs, False)
    >>> t = loader.load('parent.html')
    >>> print (t.depends) # doctest:+ELLIPSIS
    set(['.../a/new_tag.html', '.../a/layout.html', '.../b/layout.html'])
    >>> print (loader.load('index.html').depends) # doctest:+ELLIPSIS
    set(['.../a/layout.html', '.../b/layout.html'])
    >>> print (loader.load('layout.html').depends) # doctest:+ELLIPSIS
    set(['.../a/layout.html'])
    """

def test_check_expiration():
    """
    >>> dir = os.path.join(path, 'templates', 'a')
    >>> loader = Loader([dir])
    >>> f1 = open(os.path.join(dir, "a.html"), 'w')
    >>> f1.write('<h1>{{block title}}{{end}}</h1>')
    >>> f1.close()
    >>> f2 = open(os.path.join(dir, "b.html"), 'w')
    >>> f2.write('{{extend "a.html"}}{{block title}}Test1{{end}}')
    >>> f2.close()
    >>> t = loader.load('b.html')
    >>> print (t.generate())
    <h1>Test1</h1>
    """

def test_load_cache_with_expiration_check():
    """
    >>> dir = os.path.join(path, 'templates', 'a')
    >>> loader = Loader([dir], check_modified_time=True)
    >>> f1 = open(os.path.join(dir, "a.html"), 'w')
    >>> f1.write('<h1>{{block title}}a{{end}}</h1>{{include "c.html"}}')
    >>> f1.close()
    >>> f2 = open(os.path.join(dir, "b.html"), 'w')
    >>> f2.write('{{extend "a.html"}}{{block title}}Test1{{end}}')
    >>> f2.close()
    >>> f3 = open(os.path.join(dir, "c.html"), 'w')
    >>> f3.write('ccc')
    >>> f3.close()
    >>> t = loader.load('b.html')
    >>> print (t.generate())
    <h1>Test1</h1>ccc
    >>> time.sleep(1)
    >>> f4 = open(os.path.join(dir, "a.html"), 'w')
    >>> f4.write('<h2>{{block title}}a{{end}}</h2>{{include "c.html"}}')
    >>> f4.close()
    >>> t = loader.load('b.html')
    >>> print (t.generate())
    <h2>Test1</h2>ccc
    >>> time.sleep(1)
    >>> f5 = open(os.path.join(dir, "b.html"), 'w')
    >>> f5.write('{{extend "a.html"}}{{block title}}Test2{{end}}')
    >>> f5.close()
    >>> t = loader.load('b.html')
    >>> print (t.generate())
    <h2>Test2</h2>ccc
    >>> f5 = open(os.path.join(dir, "c.html"), 'w')
    >>> f5.write('ddd')
    >>> f5.close()
    >>> time.sleep(1)
    >>> t = loader.load('b.html')
    >>> print (t.generate())
    <h2>Test2</h2>ddd
    """

def test_load_cache_without_expiration_check():
    """
    >>> dir = os.path.join(path, 'templates', 'a')
    >>> loader = Loader([dir], check_modified_time=False)
    >>> f1 = open(os.path.join(dir, "a.html"), 'w')
    >>> f1.write('<h1>{{block title}}a{{end}}</h1>{{include "c.html"}}')
    >>> f1.close()
    >>> f2 = open(os.path.join(dir, "b.html"), 'w')
    >>> f2.write('{{extend "a.html"}}{{block title}}Test1{{end}}')
    >>> f2.close()
    >>> f3 = open(os.path.join(dir, "c.html"), 'w')
    >>> f3.write('ccc')
    >>> f3.close()
    >>> t = loader.load('b.html')
    >>> print (t.generate())
    <h1>Test1</h1>ccc
    >>> time.sleep(1)
    >>> f4 = open(os.path.join(dir, "a.html"), 'w')
    >>> f4.write('<h2>{{block title}}a{{end}}</h2>{{include "c.html"}}')
    >>> f4.close()
    >>> t = loader.load('b.html')
    >>> print (t.generate())
    <h1>Test1</h1>ccc
    >>> time.sleep(1)
    >>> f5 = open(os.path.join(dir, "b.html"), 'w')
    >>> f5.write('{{extend "a.html"}}{{block title}}Test2{{end}}')
    >>> f5.close()
    >>> t = loader.load('b.html')
    >>> print (t.generate())
    <h1>Test1</h1>ccc
    >>> f5 = open(os.path.join(dir, "c.html"), 'w')
    >>> f5.write('ddd')
    >>> f5.close()
    >>> time.sleep(1)
    >>> t = loader.load('b.html')
    >>> print (t.generate())
    <h1>Test1</h1>ccc
    """

def test_print_blocks():
    """
    >>> dirs = [os.path.join(path, 'templates', x) for x in ['b', 'a']]
    >>> loader = Loader(dirs, False)
    >>> loader.print_blocks('parent.html')
    -------------- Blocks --------------
        title   (templates/b/layout.html)
        content   (templates/a/layout.html)
            main   (templates/b/parent.html)
            side   (templates/a/layout.html)
    """

