#coding=utf8
from uliweb.core.taglibs import parse, Loader, parse_xml

tags = {'panel':
"""<div {%=to_attrs(_attrs, {'class':'panel'})%}>
  <div class="panel-head">
    <h3>{%<< xml(head)%}</h3>
    {% if defined('button'):%}
        {%<< xml_full('button', button)%}
    {%pass%}
  </div>
</div>""",
        'button':
"""<button class="btn btn-{%=_attrs['class']%}">{%=_text%}</button>"""
}

loader = Loader(tags=tags, tags_dir='taglibs')

def test_1():
    """
    >>> t = \"\"\"
    ... Text
    ... <t:panel a="b">
    ... <head>head</head>
    ... </t:panel>
    ... End\"\"\"
    >>> print parse(t, loader)
    <BLANKLINE>
    Text
    <div a="b" class=" panel">
      <div class="panel-head">
        <h3>head</h3>
    <BLANKLINE>
      </div>
    </div>
    End
    """

def test_2():
    """
    >>> t = '<t:button class="primary">Submit</t:button>'
    >>> print parse(t, loader)
    <button class="btn btn-primary">Submit</button>
    """

def test_3():
    """
    >>> t = \"\"\"
    ... Text
    ... <t:panel a="b">
    ... <head>head</head>
    ... <t:button class="primary">Submit</t:button>
    ... </t:panel>
    ... End\"\"\"
    >>> print parse(t, loader) # doctest: +REPORT_UDIFF
    <BLANKLINE>
    Text
    <div a="b" class=" panel">
      <div class="panel-head">
        <h3>head</h3>
    <BLANKLINE>
            <button class="btn btn-primary">Submit</button>
    <BLANKLINE>
      </div>
    </div>
    End
    """

def test_4():
    """
    >>> t = '<t:bs.button>Submit</t:bs.button>'
    >>> print parse_xml(t)
    OrderedDict([(u'bs.button', {'_text': u'Submit', '_attrs': OrderedDict()})])
    """

def test_5():
    """
    >>> t = '<t:bs.button>Submit</t:bs.button>'
    >>> print parse(t, loader)
    <button class="btn">Submit</button>
    <BLANKLINE>
    """

# t = """<t:breadcrumb>
#     <a href="#" title="Home"></a>
#     <a href="#" title="Library"></a>
#     <a active="active" title="Data"></a>
# </t:breadcrumb>"""

t = """<t:breadcrumb>
    <a href="#" title="Home">Home</a>
</t:breadcrumb>"""

# tags = {'breadcrumb':"""<ul class="breadcrumb">
#     {%for i, li in enumerate(a):
#         active = li['_attrs'].get('active')
#         title = li['_attrs'].get('title')
#         href = li['_attrs'].get('href')%}
#         {%if active:%}
#         <li class="{%=active%}">{%=title%}
#             {%if i<len(a)-1:%} <span class="divider">/</span>{%pass%}
#         </li>
#         {%else:%}
#         <li><a href="{%=href%}">{%=title%}</a>
#             {%if i<len(a)-1:%} <span class="divider">/</span>{%pass%}
#         </li>
#         {%pass%}
#     {%pass%}
# </ul>"""}

tags = {'breadcrumb':"""
{%<< xml(a)%}
"""}
loader = Loader(tags)
print parse_xml(t)
print parse(t, loader)