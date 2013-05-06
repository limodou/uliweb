#coding=utf-8
###################################################################
# Create Excel 2003 file
# Author: limodou@gmail.com
# This module need xlrd and xlwt modules
###################################################################
import xlrd
import xlwt
import datetime
import re

from xlrd import open_workbook,cellnameabs
from xlutils.copy import copy
from xlwt import Style, Formula

easyxf = xlwt.easyxf

re_link = re.compile('^<a.*?href=\"([^\"]+)\".*?>(.*?)</a>', re.DOTALL)

class ExcelWriter(object):
    def __init__(self, header=None, data=None, title=None, template=None, 
        index=0, begin_x=0, begin_y=0, hbegin_x=0, hbegin_y=0, 
        encoding='utf-8', domain=None):
        self.header = header
        self.data = data
        self.template = template
        self.title = title
        self.index = index
        self.begin_x = begin_x
        self.hbegin_x = hbegin_x
        self.begin_y = begin_y
        self.hbegin_y = hbegin_y
        self.encoding = encoding
        if domain:
            self.domain = domain.rstrip('/')
        else:
            self.domain = domain
        self.fields_list = []
        self.fields = {}
        self.field_names = []
        self.styles = {}
        
        self.init()
        self.init_styles()
        self.process_head()
        self.create_table_head()
        self.process_body()
        
    def init(self):
        if self.template:
            self.rb = open_workbook(self.template,on_demand=True,formatting_info=True)
            self.wb = copy(self.rb)
            self.sh = self.wb.get_sheet(self.index)
        else:
            self.rb = None
            self.wb = xlwt.Workbook()
            self.sh = self.wb.add_sheet(self.title or 'Sheet1')
            
    def init_styles(self):
        self.style_empty = easyxf()
        self.style_date = easyxf()
        self.style_date.num_format_str = 'YYYY-M-D'
        self.style_time = easyxf()
        self.style_time.num_format_str = 'h:mm:ss'
        self.style_datetime = easyxf()
        self.style_datetime.num_format_str = 'YYYY-M-D h:mm:ss'
        self.style_center = xlwt.Alignment()
        self.style_center.horz = xlwt.Alignment.HORZ_CENTER
        self.style_left = xlwt.Alignment()
        self.style_left.horz = xlwt.Alignment.HORZ_LEFT
        self.style_right = xlwt.Alignment()
        self.style_right.horz = xlwt.Alignment.HORZ_RIGHT
        self.style_general = xlwt.Alignment()
        self.style_general.horz = xlwt.Alignment.HORZ_GENERAL
            
    def create_table_head(self):
        from uliweb.utils.common import safe_unicode
        
        fields = []
        max_rowspan = 0
        for i, f in enumerate(self.fields_list):
            _f = list(f['title'].split('/'))
            max_rowspan = max(max_rowspan, len(_f))
            fields.append((_f, i))
        
        def get_field(fields, i, m_rowspan):
            f_list, col = fields[i]
            field = {'title':f_list[0], 'col':col, 'colspan':1, 'rowspan':1}
            if len(f_list) == 1:
                field['rowspan'] = m_rowspan
            return field
        
        def remove_field(fields, i):
            del fields[i][0][0]
        
        def clear_fields(fields):
            n = len(fields)
            for i in range(len(fields)-1, -1, -1):
                if len(fields[i][0]) == 0:
                    n = min(n, fields[i][1])
                    del fields[i]
            if len(fields):
                return fields[0][1]
            return 0
        
        n = len(fields)
        y = 0
        posx = 0
        while n>0:
            i = 0
            while i<n:
                field = get_field(fields, i, max_rowspan-y)
                remove_field(fields, i)
                j = i + 1
                while j<n:
                    field_n = get_field(fields, j, max_rowspan-y)
                    if safe_unicode(field['title']) == safe_unicode(field_n['title']) and field['rowspan'] == field_n['rowspan']:
                        #combine
                        remove_field(fields, j)
                        field['colspan'] += 1
                        j += 1
                    else:
                        break
                
                _f = self.fields[field['col']]
                y1 = self.hbegin_y + y
                y2 = y1 + field['rowspan'] - 1
#                x1 = self.hbegin_x + i + posx
                x1 = self.hbegin_x + field['col']
                x2 = x1 + field['colspan'] - 1
                self.sh.write_merge(y1, y2, x1, x2, safe_unicode(field['title']), 
                    self.style(style=_f['head_style'] or 'font: bold on;align: vert center,horz center; pattern: pattern solid, fore-colour pale_blue;borders:left thin, right thin, top thin, bottom thin;'))
                width = _f['width']
                if width and x1 == x2:
                    self.sh.col(x1).width = width*36
                
                i = j
            posx = clear_fields(fields)
            n = len(fields)
            y += 1
            
        if self.hbegin_y + y >= self.begin_y:
            self.begin_y = self.hbegin_y + y
        
    def process_head(self):
        if not self.header:
            return
        
        for i, field in enumerate(self.header):
            f = {'row':None, 'col':None, 'width':None, 
                'title':None, 'head_style':None, 'cell_style':None, 
                'name':None, 'align':'general', 'num_format':None}
            if isinstance(field, dict):
                f.update(field)
                if 'verbose_name' in field:
                    f['title'] = field['verbose_name']
            else:
                f['title'] = field
            if f['name'] is not None:
                key = f['name']
            else:
                key = i
            self.fields[i] = f
            self.fields_list.append(f)
            self.field_names.append(key)
                
    def process_body(self):
        data = self.data
        if not data:
            return
        
        for i, row in enumerate(data):
            for j, h in enumerate(self.header):
                if isinstance(row, (tuple, list)):
                    col = row[j]
                elif isinstance(row, dict):
                    col = row[h['name']]
                else:
                    raise Exception, "Can't support data format %s, only support list, tuple, dict" % type(row)
                col = row[j]
#            for j, col in enumerate(row):
#                if isinstance(col, dict):
#                    col_y = self.begin_y+(col.get('row') or i)
#                    col_x = self.begin_x+(col.get('col') or j)
#                    col_txt = col.get('text') or ''
#                    col_style = self.cell_style(j, value=col.get('text'), style=col.get('style'), align=col.get('align'))
#                else:
                col_txt = col
                col_y = self.begin_y+i
                col_x = self.begin_x+j
                col_style = self.cell_style(j, value=col)
                  
                if isinstance(col_txt, str):
                    col_txt = unicode(col_txt, self.encoding)
                elif hasattr(col_txt, '__unicode__'):
                    col_txt = unicode(col_txt)
                if isinstance(col_txt, unicode):
                    r = re_link.search(col_txt)
                    if r:
                        self.hyperlink(col_y, col_x, r.group(2), r.group(1))
                        continue
                self.sh.write(col_y, col_x, col_txt, col_style)
         
    def style(self, value=None, style=None, align=None, num_format=None):
        if isinstance(style, str):
            if style not in self.styles:
                s = easyxf(style)
                self.styles[style] = s
            else:
                s = self.styles[style]
        elif isinstance(style, dict):
            s = easyxf(**style)
        else:
            if isinstance(value, datetime.date):
                s = self.style_date
            elif isinstance(value, datetime.time):
                s = self.style_time
            elif isinstance(value, datetime.datetime):
                s = self.style_datetime
            else:
                s = self.style_empty
        if align:
            if align == 'center':
                s.alignment = self.style_center
            elif align == 'left':
                s.alignment = self.style_left
            elif align=='right':
                s.alignment = self.style_right
            else:
                s.alignment = self.style_general
        if num_format:
            s.num_format_str = num_format
        return s
    
    def cell_style(self, col=None, value=None, style=None, align=None, num_format=None):
        if style:
            return self.style(style=style, align=align, num_format=num_format)
        
        s = self.style(value=value)
        if self.header:
            f = self.fields.get(col)
            s = self.style(value=value, style=f['cell_style'], align=f['align'], num_format=f['num_format'])
        return s
        
    def save(self, filename):
        self.wb.save(filename)
        
    def hyperlink(self, row, col, title, link, style=None):
        import urlparse
        
        style = style or 'font: underline single,color 4'
        style = self.style(style=style)
        
        r = urlparse.urlparse(link)
        if not r.scheme and self.domain:
            link = self.domain + link
        title = title.replace('"', '')
        self.sh.write(row, col, Formula('HYPERLINK("%s";"%s")' % (link, title)), style)
        
if __name__ == '__main__':
    import datetime
#    w = ExcelWriter(template='a.xls')
#    w.save('b.xls')
    header = [{'width':100, 'title':'名字'},
        {'width':40, 'title':'信息/人员/年龄', 'align':'left'},
        {'width':40, 'title':'信息/人员/aaaa'},
        {'width':80, 'title':'信息/日期'},
        {'title':'链接'}]
    data = [
        ('中文', 12, 12.3, datetime.datetime(2011, 7, 11), '<a href="http://google.com">google.com</a>'),
    ]
    def get_data():
        for i in range(1000):
            yield ('中文', i, 12.3, datetime.datetime(2011, 7, 11), '<a href="http://google.com?id=1" target="_blank">google.com</a>')
    w = ExcelWriter(header=header, data=get_data())
    w.save('c.xls')