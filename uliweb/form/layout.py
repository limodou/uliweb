from __future__ import with_statement
from uliweb.i18n import gettext_lazy as _

__all__ = ['Layout', 'TableLayout', 'CSSLayout', 
    'BootstrapLayout', 'BootstrapTableLayout']

from uliweb.core.html import Buf, Tag, Div

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
    form_class = ''
    
    def __init__(self, form, layout=None, **kwargs):
        self.form = form
        self.layout = layout
        self.kwargs = kwargs
        self.init()

    def init(self):
        pass

    def html(self):
        return '\n'.join([x for x in [self.begin(), self.hiddens(), self.body(), self.buttons_line(), self.end()] if x])
    
    def __str__(self):
        return self.html()
    
    def get_widget_name(self, f):
        return f.build.__name__

    def is_hidden(self, f):
        return f.type_name == 'hidden' or f.hidden
    
    def begin(self):
        if not self.form.html_attrs['class'] and self.form_class:
            self.form.html_attrs['class'] = self.form_class
        return self.form.form_begin
    
    def hiddens(self):
        s = []
        for name, obj in self.form.fields_list:
            f = getattr(self.form, name)
            if self.is_hidden(obj):
                s.append(str(f))
        return ''.join(s)
    
    def body(self):
        return ''
    
    def end(self):
        return self.form.form_end
    
    def _buttons_line(self, buttons):
        return ' '.join([str(x) for x in buttons])
    
    def buttons_line(self):
        return str(self._buttons_line(self.form.get_buttons()))
    
    def buttons(self):
        return ' '.join([str(x) for x in self.form.get_buttons()])
    
class TableLayout(Layout):
    field_classes = {
        ('Text', 'Password', 'TextArea'):'type-text',
        ('Button', 'Submit', 'Reset'):'type-button',
        ('Select', 'RadioSelect'):'type-select',
        ('Radio', 'Checkbox'):'type-check',
        }
    form_class = 'tform'
    buttons_line_class = 'type-button'
    
    def __init__(self, form, layout=None, label_fix=False, table_class='table table-layout width100'):
        self.form = form
        self.layout = layout
        self.label_fix = label_fix
        self.table_class = table_class

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

        tr = Tag('tr', newline=True)
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
                
                #process hidden field
                if self.is_hidden(obj):
                    #tr << f
                    continue
                
                _class = self.get_class(obj)
                if f.error:
                    _class = _class + ' error'
                
                with tr.td(colspan=_span, width='%d%%' % (100*_span/n,), valign='top'):
                    with tr.Div(_class=_class, id='div_'+obj.id):
                        if f.error:
                            tr.strong(f.error, _class="message")
                        if self.get_widget_name(obj) == 'Checkbox':
                            tr << f
                            tr << f.label
                            tr << f.help_string or '&nbsp;'
                        else:
                            if self.label_fix:
                                tr << f.field.get_label(_class='field label_fix')
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

    def _buttons_line(self, buttons):
        div = Div(_class=self.buttons_line_class)
        with div:
            div << buttons
        return div
        
    def body(self):
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
        cls = self.table_class
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
                    first = False
                    continue
                else:
                    fields = [fields]
            if first:
                first = False
                buf << '<table class="%s"><tbody>' % cls
                table = True
            buf << self.line(fields, n)
            
        #close the tags
        if table:
            buf << '</tbody></table>'
        if fieldset:
            buf << '</fieldset>'
        
        return str(buf)
        
class CSSLayout(Layout):
    def line(self, obj, label, input, help_string='', error=None):
        div = Div()
        div << label
        div << input
        if error:
            div << Tag('span', error, _class='error')
        div << Tag('br/')
        return div

    def _buttons_line(self, buttons):
        div = Div()
        div << Tag('label', '&nbsp;')
        div << buttons
        div << Tag('br/')
        return div

    def body(self):
        buf = Buf()
        
        if self.form.fieldset:
            form = buf << Tag('fieldset')
            if self.form.form_title:
                form << Tag('legend', self.form.form_title)
        else:
            form = buf
    
        for name, obj in self.form.fields_list:
            f = getattr(self.form, name)
            if self.is_hidden(obj):
                #form << f
                pass
            else:
                form << self.line(obj, f.label, f, f.help_string, f.error)
        
        return str(buf)

class QueryLayout(Layout):
    form_class = 'form'
    
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

    def body(self):
        buf = Buf()
        self.process_layout(buf)
        return str(buf)
    
    def buttons_line(self):
        return ''

    def process_layout(self, buf):
        def output(buf, line, first=False, more=False):
            if isinstance(line, (tuple, list)):
                with buf.table(_class='query'):
                    with buf.tr:
                        for x in line:
                            f = getattr(self.form, x, None)
                            if f:
                                obj = self.form.fields[x]
                                if self.is_hidden(obj):
                                    #buf << f
                                    pass
                                else:
                                    buf << self.line(obj, f.label, f, f.help_string, f.error)
                            elif x:
                                with buf.td:
                                    buf << x
                        if first:
                            with buf.td:
                                buf << self.form.get_buttons()
                                if more:
                                    buf << self.get_more_button()
                            
            else:
                f = getattr(self.form, line)
                obj = self.form.fields.get(line)
                if obj and self.is_hidden(obj):
                    #buf << f
                    pass
                else:
                    with buf.table(_class='query'):
                        with buf.tr:
                            if obj:
                                buf << self.line(obj, f.label, f, f.help_string, f.error)
                            elif line:
                                with buf.td:
                                    buf << line
                            if first:
                                with buf.td:
                                    buf << self.form.get_buttons()
                                    if more:
                                        buf << self.get_more_button()
                                    
        if not self.layout:
            self.layout = [[name for name, obj in self.form.fields_list]]
        if self.layout:
            line = self.layout[0]
            first = True
            layout = self.layout[1:]
            more = bool(layout)
            output(buf, line, first=first, more=more)
            if more:
                with buf.Div(id='query_div'):
                    for line in layout:
                        output(buf, line)
                buf << self.post_layout()
                
    def get_more_button(self):
        return '<a href="#" id="more_query">%s</a>' % _('more')
    
    def post_layout(self):
        return ''

class BootstrapLayout(Layout):
    form_class = 'form-horizontal'
    field_classes = {
        ('Text', 'Password', 'TextArea'):'input-xlarge',
        ('Button', 'Submit', 'Reset', 'Checkbox', 'File', 'Hidden'):'',
        ('Select', 'RadioSelect'):'',
        ('Radio',):'radio',
        }
    
    def line(self, obj, label, input, help_string='', error=None):
        
        _class = "control-group"
        if error:
            _class = _class + ' error'
        
        div_group = Div(_class=_class, id='div_'+obj.id, newline=True)
        with div_group: 
            div_group << input.get_label(_class='control-label')
            div = Div(_class='controls', newline=True)
            with div:
                div << input                    
                div << Tag('p', _class="help help-block", _value=help_string)
                if error:
                    div << Div(_class="message help-block", _value=error, newline=True)
                    
            div_group << str(div)
        return str(div_group)
    
    def _buttons_line(self, buttons):
        div = Div(_class="form-actions")
        with div:
            div << buttons
        return div
    
    def body(self):
        buf = Buf()
        if not self.layout:
            self.layout = [name for name, obj in self.form.fields_list]
        self.process_layout(buf)
        return str(buf)

    def process_layout(self, buf):
        if self.form.form_title:
            buf << '<fieldset><legend>%s</legend>' % self.form.form_title
        for line in self.layout:
            if isinstance(line, (tuple, list)):
                with buf.Div(_class='line'):
                    for x in line:
                        f = getattr(self.form, x)
                        obj = self.form.fields[x]
                        if self.is_hidden(obj):
                            #buf << f
                            pass
                        else:
                            buf << self.line(obj, f.label, f, f.help_string, f.error)
            else:
                f = getattr(self.form, line)
                obj = self.form.fields[line]
                if self.is_hidden(obj):
                    #buf << f
                    pass
                else:
                    buf << self.line(obj, f.label, f, f.help_string, f.error)
        if self.form.form_title:
            buf << '</fieldset>'

class BootstrapTableLayout(TableLayout):
    field_classes = {
        ('Text', 'Password', 'TextArea'):'input-xlarge',
        ('Button', 'Submit', 'Reset', 'Checkbox', 'Hidden', 'File'):'',
        ('Select', 'RadioSelect'):'',
        ('Radio',):'radio',
        }
    
    form_class = 'form-horizontal'
    buttons_line_class = 'form-actions'
    
    def line(self, fields, n):
        _x = 0
        for _f in fields:
            if isinstance(_f, (str, unicode)):
                _x += 1
            elif isinstance(_f, dict):
                _x += _f.get('colspan', 1)
            else:
                raise Exception, 'Colume definition is not right, only support string or dict'
            
        tr = Tag('tr', newline=True)
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
                
                #process hidden field
                if self.is_hidden(obj):
                    #tr << f
                    continue
                
                _class = "control-group"
                if f.error:
                    _class = _class + ' error'
                
                with tr.td(colspan=_span, width='%d%%' % (100*_span/n,), valign='top'):
                    with tr.Div(_class=_class, id='div_'+obj.id):
                        if self.get_widget_name(obj) == 'Checkbox':
                            tr << "&nbsp"
                        else:
                            if self.label_fix:
                                tr << f.field.get_label(_class='label_fix')
                            else:
                                tr << f.get_label(_class='control-label')                            
                            
                        div = Div(_class='controls')
                        with div:
                            if self.get_widget_name(obj) == 'Checkbox':
                                div << f
                                div << f.label
                            else:
                                div << f                    
                            div << Div(_class="help help-block", _value= f.help_string or '')
                            if f.error:
                                div << Div(_class="message help-block", _value=f.error)
                        tr << str(div)
        return tr
    
