from __future__ import with_statement
from uliweb.i18n import gettext_lazy as _

__all__ = ['Layout', 'TableLayout', 'CSSLayout', 'YamlLayout']

from uliweb.core.html import Buf, Tag

def min_times(num):
    def _f(m, n):
        r = m*n
        while 1:
            if m==n:
                return r/m
            elif m>n:
                m -= n
            else:
                n -= m
    num = set(num)
    return reduce(_f, num)

class Layout(object):
    def __init__(self, form, layout=None):
        self.form = form
        self.layout = layout
        
    def html(self):
        return ''
    
    def __str__(self):
        return self.html()
    
    def get_widget_name(self, f):
        return f.build.__name__
    
    def is_hidden(self, f):
        return self.get_widget_name(f) == 'Hidden'
    
class TableLayout(Layout):
#    def line(self, label, input, help_string='', error=None):
    field_classes = {
        ('Text', 'Password', 'TextArea'):'type-text',
        ('Button', 'Submit', 'Reset'):'type-button',
        ('Select', 'RadioSelect'):'type-select',
        ('Radio', 'Checkbox'):'type-check',
        }
    
    def get_class(self, f):
        name = f.build.__name__
        _class = 'type-text'
        for k, v in self.field_classes.items():
            if name in k:
                _class = v
                break
        return _class

    def line(self, fields, n):
        _x = 0
        for _f in fields:
            if isinstance(_f, (str, unicode)):
                _x += 1
            elif isinstance(_f, dict):
                _x += _f.get('colspan', 1)
            else:
                raise Exception, 'Colume definition is not right, only support string or dict'

        tr = Tag('tr')
        with tr:
            for x in fields:
                _span = n / _x
                if isinstance(x, (str, unicode)):
                    name = x
                elif isinstance(x, dict):
                    name = x['name']
                    _span = _span * x.get('colspan', 1)

                f = getattr(self.form, name)
                obj = self.form.fields[name]
                _class = self.get_class(obj)
                if f.error:
                    _class = _class + ' error'
                
                with tr.td(colspan=_span, width='%d%%' % (100*_span/n,), valign='top'):
                    with tr.div(_class=_class):
                        if f.error:
                            tr.strong(f.error, _class="message")
                        if self.get_widget_name(obj) == 'Checkbox':
                            tr << f
                            tr << f.label
                            tr << f.help_string or '&nbsp;'
                        else:
                            tr << f.label
                            tr << f
                            tr << f.help_string or '&nbsp;'
                
        return tr

    def single_line(self, element):
        with tr:
            with tr.td(colspan=3):
                tr << element
        return tr

    def buttons_line(self, buttons, n):
        tr = Tag('tr', align='center', _class="buttons")
        with tr:
            with tr.td(colspan=n, align='left'):
                tr << Tag('label', '&nbsp;', _class='field')
                tr << buttons
        return tr
        
    def html(self):
        if 'tform' not in self.form.html_attrs['_class']:
            self.form.html_attrs['_class'] = 'tform'
        if self.layout:
            m = []
            for line in self.layout:
                if isinstance(line, (tuple, list)):
                    _x = 0
                    for f in line:
                        if isinstance(f, (str, unicode)):
                            _x += 1
                        elif isinstance(f, dict):
                            _x += f.get('colspan', 1)
                        else:
                            raise Exception, 'Colume definition is not right, only support string or dict'
                    m.append(_x)
                else:
                    m.append(1)
            n = min_times(m)
        else:
            self.layout = [name for name, obj in self.form.fields_list]
            n = 1
            
        buf = Buf()
        table = None
        fieldset = None
        first = True
        buf << self.form.form_begin
        cls = 'width100'
        for fields in self.layout:
            if not isinstance(fields, (tuple, list)):
                if isinstance(fields, (str, unicode)) and fields.startswith('--') and fields.endswith('--'):
                    #THis is a group line
                    if table:
                        buf << '</tbody></table>'
                    if fieldset:
                        buf << '</fieldset>'
                    title = fields[2:-2].strip()
                    if title:
                        fieldset = True
                        buf << '<fieldset><legend>%s</legend>' % title
                    
                    buf << '<table class="%s"><tbody>' % cls
                    table = True
                    first = True
                    continue
                else:
                    fields = [fields]
            if first:
                first = False
                buf << '<table class="%s"><tbody>' % cls
                table = True
            buf << self.line(fields, n)
            
        buf << self.buttons_line(self.form.get_buttons(), n)
        
        #close the tags
        if table:
            buf << '</tbody></table>'
        if fieldset:
            buf << '</fieldset>'
        
        buf << self.form.form_end
        return str(buf)
        
#        with buf.table(_class='table'):
#            with buf.tbody:
#
#                for fields in self.layout:
#                    if not isinstance(fields, (tuple, list)):
#                        fields = [fields]
#                    buf << self.line(fields, n)
#        
#                buf << self.buttons_line(self.form.get_buttons(), n)
#                
#            buf << self.form.form_end
#        return str(buf)
    
class CSSLayout(Layout):
    def line(self, obj, label, input, help_string='', error=None):
        div = Buf()
        div << label
        div << input
        if error:
            div << Tag('span', error, _class='error')
        div << Tag('br/')
        return div

    def buttons_line(self, buttons):
        div = Buf()
        div << Tag('label', '&nbsp;', _class='field')
        div << buttons
        div << Tag('br/')
        return div

    def html(self):
        buf = Buf()
        buf << self.form.form_begin
        
        if self.form.fieldset:
            form = buf << Tag('fieldset')
            if self.form.form_title:
                form << Tag('legend', self.form.form_title)
        else:
            form = buf
    
        for name, obj in self.form.fields_list:
            f = getattr(self.form, name)
            if self.is_hidden(obj):
                form << f
            else:
                form << self.line(obj, f.label, f, f.help_string, f.error)
        
        form << self.buttons_line(self.form.get_buttons())
        buf << self.form.form_end
        return str(buf)

class QueryLayout(Layout):
    def line(self, obj, label, input, help_string='', error=None):
        buf = Buf()
        with buf.td:
            buf << label
        
        if error:
            with buf.td(_class='error'):
                buf << input
                buf << error
        else:
            with buf.td:
                buf << input
        return buf

    def html(self):
        buf = Buf()
        buf << self.form.form_begin
        self.process_layout(buf)
        buf << self.form.form_end
        return str(buf)
    
    def process_layout(self, buf):
            
        def output(buf, line, first=False, more=False):
            if isinstance(line, (tuple, list)):
                with buf.table(_class='query'):
                    with buf.tr:
                        for x in line:
                            f = getattr(self.form, x)
                            obj = self.form.fields[x]
                            if self.is_hidden(obj):
                                buf << f
                            else:
                                buf << self.line(obj, f.label, f, f.help_string, f.error)
                        if first:
                            with buf.td:
                                buf << self.form.get_buttons()
                                if more:
                                    buf << '<a href="javascript:void(0)" id="more_query">%s</a>' % _('more')
                            
            else:
                f = getattr(self.form, line)
                obj = self.form.fields[line]
                if self.is_hidden(obj):
                    buf << f
                else:
                    with buf.table(_class='query'):
                        with buf.tr:
                            buf << self.line(obj, f.label, f, f.help_string, f.error)
                            
                            if first:
                                with buf.td:
                                    buf << self.form.get_buttons()
                                    if more:
                                        buf << '<a href="#" id="more_query">more</a>'
                                    
        if not self.layout:
            self.layout = [[name for name, obj in self.form.fields_list]]
        if self.layout:
            line = self.layout[0]
            first = True
            layout = self.layout[1:]
            more = bool(layout)
            output(buf, line, first=first, more=more)
            if more:
                with buf.div(id='query_div'):
                    for line in layout:
                        output(buf, line)

from widgets import RadioSelect, Radio

class YamlRadioSelect(RadioSelect):
    def html(self):
        s = Buf()
        for v, caption in self.choices:
            args = {'value': v}
            id = args.setdefault('id', 'radio_%d' % self.get_id())
            args['name'] = self.kwargs.get('name')
            if v == self.value:
                args['checked'] = None
            div = Tag('div', _class='type-check')
            div << Radio(**args)
            div << Tag('label', caption, _for=id)
            s << div
        return str(s)
    
class YamlLayout(Layout):
    field_classes = {
        ('Text', 'Password', 'TextArea'):'type-text',
        ('Button', 'Submit', 'Reset'):'type-button',
        ('Select', 'RadioSelect'):'type-select',
        ('Radio', 'Checkbox'):'type-check',
        }

    def get_class(self, f):
        name = f.build.__name__
        _class = 'type-text'
        for k, v in self.field_classes.items():
            if name in k:
                _class = v
                break
        return _class
    
    def line(self, obj, label, input, help_string='', error=None):
        _class = self.get_class(obj)
        if error:
            _class = _class + ' error'
        
        if self.get_widget_name(obj) == 'RadioSelect':
            obj.build = YamlRadioSelect
            fs = Tag('fieldset')
            fs << Tag('legend', label)
            fs << input
            return fs
        else:
            div = Tag('div', _class=_class)
            with div:
                if error:
                    div.strong(error, _class="message")
                if self.get_widget_name(obj) == 'Checkbox':
                    div << input
                    div << label
                    div << help_string
                else:
                    div << label
                    div << help_string
                    div << input
            return div

    def buttons_line(self, buttons):
        div = Tag('div', _class='line')
        with div:
            with div.div(_class='type-button'):
                div << buttons
        return str(div)

    def html(self):
        buf = Buf()
        if 'yform' not in self.form.html_attrs['_class']:
            self.form.html_attrs['_class'] = 'yform'
        buf << self.form.form_begin
            
#            if self.form.fieldset:
#                with buf.fieldset:
##                form = buf << Tag('fieldset')
#                    if self.form.form_title:
#                        buf.legend(self.form.form_title)
##            else:
##                form = buf
        if not self.layout:
            self.layout = [name for name, obj in self.form.fields_list]
        self.process_layout(buf)
        
        buf << self.buttons_line(self.form.get_buttons())
        buf << self.form.form_end
        return str(buf)

    def process_layout(self, buf):
        for line in self.layout:
            if isinstance(line, (tuple, list)):
                with buf.div(_class='line'):
                    for x in line:
                        f = getattr(self.form, x)
                        obj = self.form.fields[x]
                        if self.is_hidden(obj):
                            buf << f
                        else:
                            buf << self.line(obj, f.label, f, f.help_string, f.error)
            else:
                f = getattr(self.form, line)
                obj = self.form.fields[line]
                if self.is_hidden(obj):
                    buf << f
                else:
                    buf << self.line(obj, f.label, f, f.help_string, f.error)
                    
