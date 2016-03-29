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

# def test_3():
#     """
#     >>> t = \"\"\"
#     ... Text
#     ... <t:panel a="b">
#     ... <head>head</head>
#     ... <t:button class="primary">Submit</t:button>
#     ... </t:panel>
#     ... End\"\"\"
#     >>> print parse(t, loader) # doctest: +REPORT_UDIFF
#     <BLANKLINE>
#     Text
#     <div a="b" class=" panel">
#       <div class="panel-head">
#         <h3>head</h3>
#     <BLANKLINE>
#             <button class="btn btn-primary">Submit</button>
#     <BLANKLINE>
#       </div>
#     </div>
#     End
#     """

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

def test_6():
    """
    >>> t = \"\"\"<t:form_input_field name="title" label="label" required="required">
    ...     <input type="text" value="value" placeholder="placeholder" help="help">
    ...     <![CDATA[
    ...     <h3>CDATA</h3>
    ...     ]]>
    ...     </input>
    ... </t:form_input_field>
    ... \"\"\"
    >>> print parse_xml(t)
    OrderedDict([(u'form_input_field', {u'input': {'_text': u'<h3>CDATA</h3>', '_attrs': OrderedDict([(u'type', u'text'), (u'value', u'value'), (u'placeholder', u'placeholder'), (u'help', u'help')])}, '_text': u'', '_attrs': OrderedDict([(u'name', u'title'), (u'label', u'label'), (u'required', u'required')])})])
    """

def test_6_1():
    """
    >>> t = \"\"\"<t:form_input_field name="title" label="label" required="required">
    ...     <input type="text" value="value" placeholder="placeholder" help="help">
    ...     <![[
    ...     <h3>CDATA</h3>
    ...     ]]>
    ...     </input>
    ... </t:form_input_field>
    ... \"\"\"
    >>> print parse_xml(t)
    OrderedDict([(u'form_input_field', {u'input': {'_text': u'<h3>CDATA</h3>', '_attrs': OrderedDict([(u'type', u'text'), (u'value', u'value'), (u'placeholder', u'placeholder'), (u'help', u'help')])}, '_text': u'', '_attrs': OrderedDict([(u'name', u'title'), (u'label', u'label'), (u'required', u'required')])})])
    """

def test_7():
    """
    >>> t = '<t:bs.button class="{{<< 123}}">Submit</t:bs.button>'
    >>> print parse(t, loader)
    <button class="btn btn-{{<< 123}}">Submit</button>
    <BLANKLINE>
    """

def test_8():
    """
    >>> t = \'\'\'<t:bs.button class="{{<< 123}}">Submit
    ... <!-- <a href="#">aaa</a> -->
    ... </t:bs.button>\'\'\'
    >>> print parse(t, loader)
    <button class="btn btn-{{<< 123}}">Submit</button>
    <BLANKLINE>
    """

# t = """<t:breadcrumb>
#     <a href="#" title="Home"></a>
#     <a href="#" title="Library"></a>
#     <a active="active" title="Data"></a>
# </t:breadcrumb>"""

# t = """<t:form_input_field name="title" label="label" required="required">
#     <input type="text" value="value" placeholder="placeholder" help="help">
#     <![CDATA[
#     <h3>CDATA</h3>
#     ]]>
#     </input>
# </t:form_input_field>
# """

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

# import logging
# logging.basicConfig(level=logging.INFO)
# log = logging.getLogger()
#
# tags = {'form_input_field':"""
# {%name=_attrs['name']%}
#
# <div class="control-group" id="div_field_{%=name%}">
#     {%if _attrs.get('label'):%}
#     <label class="control-label" for="field_{%=name%}">{%=_attrs['label']%}
#         {%if _attrs.get('required'):%}
#         :<span class="field_required">*</span>
#         {%pass%}
#     </label>
#     {%pass%}
#     <div class="controls">
#         {%
#             type = input['_attrs'].pop('type', 'text')
#             help = input['_attrs'].pop('help', '')
#         %}
#         <input id="field_{%=name%}"
#                name="{%=name%}"
#                type="{%=type%}"
#                {%=to_attrs(input['_attrs'])%}></input>
#         {%if help:%}
#         <p class="help help-block">{%<< help%}</p>
#         {%pass%}
#     </div>
# </div>
# """}
# loader = Loader(tags)
# print parse_xml(t)
# print parse(t, loader, log=log)


