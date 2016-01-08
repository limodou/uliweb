#coding=utf8
#xlsx模板处理

import os
import re
import shutil
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from pprint import pprint
from copy import deepcopy
import datetime
from uliweb.utils.common import safe_unicode

re_filter = re.compile(r'(\w+)(?:\((.*?)\))?')

def _date(cell, data, f, _var=None, _sh=None):
    f = f or 'yyyy-mm-dd'
    cell.value = data
    cell.number_format = f
    return cell.value

def _link(cell, data, text, _var=None, _sh=None):
    t = safe_unicode(text).format(**_var)
    cell.value = data
    cell.hyperlink = t
    return cell.value

def _validate_list(cell, data, _list, blank=True, _var=None, _sh=None):
    cell.value = data
    dv = DataValidation(type="list", formula1='"{}"'.format(_list), allow_blank=blank)
    _sh.add_data_validation(dv)
    dv.add(cell)
    return cell.value

env = {'date':_date, 'datetime':datetime, 'link':_link,
       'validate_list':_validate_list}

class Converter(object):
    """
    Parse expr|filter|filter(args)
    """
    def __init__(self, text):
        self.text = text
        self.expr = ''
        self.filter = []
        self.parse()

    def parse(self):
        for i, c in enumerate(self.text.split('|')):
            c = c.strip()
            if i == 0:
                self.expr = c
            else:
                if '(' in c:
                    b = re_filter.match(c)
                    if b:
                        f = u'{0}(cell, value, {1}, _var=_var, _sh=_sh)'.format(b.group(1), b.group(2))
                    else:
                        raise ValueError("Filter {} format is not right.".format(c))
                else:
                    f = u'{}(cell, value, _var=_var, _sh=_sh)'.format(c)
                self.filter.append(f)

    def __call__(self, cell, data, env, sheet=None):
        d = data.copy()
        d['cell'] = cell

        if self.expr:
            value = eval(self.expr, env, data)
        else:
            value = self.expr

        d['value'] = value
        d['_var'] = d
        d['_sh'] = sheet
        cell.value = value
        for f in self.filter:
            d['value'] = eval(f, d, env)
        return d['value']


class WriteTemplate(object):
    def __init__(self, sheet):
        self.sheet = sheet
        self.size = (len(sheet.rows), len(sheet.columns))
        self.template = self.get_template()
        self.row = 0

    def get_style(self, cell):
        return {'font':cell.font, 'border':cell.border, 'fill':cell.fill,
                 'alignment':cell.alignment, 'protection':cell.protection,
                 'number_format':cell.number_format,
                 }

    def set_style(self, cell, style):
        for k, v in style.items():
            setattr(cell, k, v)

    def get_template(self):
        """
        读取一个Excel模板，将此Excel的所有行读出来，并且识别特殊的标记进行记录

        :return: 返回读取后的模板，结果类似：

        [
            {'cols': #各列,与subs不会同时生效
             'subs':[ #子模板
                    {'cols':#各列,
                     'subs': #子模板
                     'field': #对应数据中字段名称
                    },
                    ...
                ]
             'field': #对应数据中字段名称
            },
            ...
        ]

        子模板的判断根据第一列是否为 {{for field}} 来判断，结束使用 {{end}}
        """
        rows = []
        stack = []
        stack.append(rows)
        #top用来记录当前栈
        top = rows
        for i in range(1, len(self.sheet.rows)+1):
            cell = self.sheet.cell(row=i, column=1)
            #是否子模板开始
            if (isinstance(cell.value, (str, unicode)) and
                    cell.value.startswith('{{for ') and
                    cell.value.endswith('}}')):
                row = {'field':cell.value[6:-2].strip(), 'cols':[], 'subs':[]}
                top.append(row)
                top = row['subs']
                stack.append(top)
            #是否子模板结束
            elif (isinstance(cell.value, (str, unicode)) and
                    cell.value == '{{end}}'):
                stack.pop()
                top = stack[-1]
            else:
                row = {'cols':[], 'subs':[]}
                cols = row['cols']
                for j in range(1, len(self.sheet.columns)+1):
                    cell = self.sheet.cell(row=i, column=j)
                    v = self.process_cell(i, j, cell)
                    if v:
                        cols.append(v)
                if row['cols'] or row['subs']:
                    top.append(row)


        # pprint(rows)
        return rows

    def parse_cell(self, cell):
        """
        Process cell field, the field format just like {{field}}
        :param cell:
        :return: value, field
        """
        field = ''
        if (isinstance(cell.value, (str, unicode)) and
            cell.value.startswith('{{') and
            cell.value.endswith('}}')):
            field = cell.value[2:-2].strip()
            value = ''
        else:
            value = cell.value

        return value, field

    def process_cell(self, row, column, cell):
        value, field = self.parse_cell(cell)
        if field:
            converter = Converter(field)
        else:
            converter = None

        return {'value':value, 'converter':converter, 'col':column,
                'style':self.get_style(cell)}

    def write(self, sheet, data):
        for v in data:
            self.row += 1
            v['row'] = self.row
            self.write_single(sheet, v)

        i = self.row
        while i < self.size[0] + 1:
            for j in range(self.size[1]):
                cell = sheet.cell(row=i, column=j+1)
                cell.value = None
            i += 1
        self.sheet._garbage_collect()


    def write_line(self, sheet, row, data):
        """

        :param sheet:
        :param row: template row
        :param data:
        :return:
        """
        for i, d in enumerate(row['cols']):
            c = sheet.cell(row=self.row, column=i+1)
            self.write_cell(sheet, c, d, data)
        self.row += 1

    def write_cell(self, sheet, cell, column, data):
        self.set_style(cell, column['style'])
        if column['converter']:
            value = column['converter'](cell, data, env, sheet)
        else:
            value = column['value']
            cell.value = value

    def write_single(self, sheet, data):
        """

        :param sheet:
        :param data: 报文对象， dict
        :param template:
        :return:
        """
        # if not get_data:
        #     def get_data(x):
        #         # print '=====', x
        #         for i in x:
        #             yield i
        #             if 'children' in i and i['children']:
        #                 for j in get_data(i['children']):
        #                     yield j
        #
        def _subs(sheet, subs, data):
            for d in data:
                if d:
                    for line in subs:
                        self.write_line(sheet, line, d)

        for line in self.template:
            if line['subs']:
                loop_name = line['field']
                d = data.get(loop_name, [{}])
                _subs(sheet, line['subs'], d)
            else:
                self.write_line(sheet, line, data)

class ReadLines(object):
    def __init__(self, sheet, start=1):
        self.line = start
        self.size = len(sheet.rows)

    def next(self):
        if self.line < self.size:
            self.line += 1
        else:
            self.line = None
        return self.line

    def row(self):
        return self.rows[self.line-1]

class ReadTemplate(WriteTemplate):
    def process_cell(self, row, column, cell):
        """
        对于读模板，只记录格式为 {{xxx}} 的字段
        :param cell:
        :return: 如果不是第一行，则每列返回{'col':列值, 'field'}，否则只返回 {'value':...}
        """
        value, field = self.parse_cell(cell)

        if value or field:
            return {'col':column, 'field':field, 'value':value}
        else:
            return {}

    def match(self, row, template_row=None):
        """
        匹配一个模板时，只比较起始行，未来考虑支持比较关键字段即可，现在是起始行的所有字段全匹配
        :param row:
        :return:
        """
        if not template_row:
            template_cols = self.template[0]['cols']
        else:
            template_cols = template_row['cols']

        #check if length of template_cols great than row, then match failed
        if len(template_cols)>len(row):
            return False

        for c in template_cols:
            #如果坐标大于模板最大长度，则表示不匹配，则退出
            text = c['value']
            if not text or (text and not (text.startswith('{{') and text.endswith('}}'))
                and row[c['col']-1].value == text):
                pass
            else:
                return False
        # print 'Matched'
        return True


    def extract_data(self, sheet, line):

        def _get_line(line, row):
            d = {}
            for c in row['cols']:
                if c['field']:
                    cell = sheet.cell(row=line, column=c['col'])
                    if isinstance(cell.value, (str, unicode)):
                        v = cell.value.strip()
                    else:
                        v = cell.value
                    d[c['field']] = v
            return d

        def _subs(line, subs, nextrow):
            data = []
            while line:
                if not nextrow or (nextrow and not self.match(sheet.rows[line-1], nextrow)):
                    d = {}
                    for r in subs:
                        _d = _get_line(line, r)
                        d.update(_d)
                        line = line_iter.next()
                    if d:
                        data.append(d)
                else:
                    break
            return data

        line_iter = ReadLines(sheet, line)
        result = []
        data = {}

        while line_iter.line is not None:
            n = 0
            data = {}
            while line_iter.line and n < len(self.template):
                row = self.template[n]
                if row['subs']:
                    if n == len(self.template) - 1:
                        nextrow = self.template[0]
                    else:
                        nextrow = self.template[n+1]
                    data[row['field']] = _subs(line_iter.line, row['subs'], nextrow)
                else:
                    d = _get_line(line_iter.line, row)
                    if d:
                        data.update(d)
                    line_iter.next()

                n += 1

            if data:
                result.append(data)

        return result

    def get_data(self, sheet, multi=False):
        line = 1
        size = len(sheet.rows)
        while line <= size:
            if self.match(sheet.rows[line-1]):
                d = self.extract_data(sheet, line)
                return d
            else:
                line += 1
        return []

class Writer(object):
    def __init__(self, template_file, sheet_name, output_file, data, create=True):
        self.template_file = template_file
        self.output_file = output_file
        self.sheet_name = sheet_name
        self.data = data
        self.create = create
        self.row = 0

        self.init()

    def init(self):

        if self.create or not os.path.exists(self.output_file):
            shutil.copy(self.template_file, self.output_file)
        wb1 = load_workbook(self.template_file)
        template = self.get_template(wb1)

        wb2 = load_workbook(self.output_file)
        template.write(wb2[self.sheet_name], self.data)

        wb2.save(self.output_file)

    def get_template(self, workbook):
        sheet = workbook[self.sheet_name]
        t = WriteTemplate(sheet)
        return t



class Reader(object):
    def __init__(self, template_file, sheet_name, input_file,
                 use_merge=False, merge_keys=None, merge_left_join=True,
                 merge_verbose=False, callback=None):
        """

        :param template_file:
        :param sheet_name:
        :param input_file: 输入文件可以是一个list或tuple数组,如果是tuple数组,格式为:
                [('filename', '*'), ('filename', 'sheetname1', 'sheetname2'), 'filename']
                第一个为文件名,后面的为sheet页名称,'*'表示通配符,如果和sheet_name相同,则可以仅为字符串

                如果input_file中不存在指定的Sheet,则自动取所有sheets
        :param use_merge: If use Merge to combine multiple data
        :param merge_keys: keys parameter used in Merge
        :param merge_left_join: left_join parameter used in Merge
        :param merge_verbose: verbose parameter used in Merge
        :param callback: callback function used after combine data, the callback function
                should be:

                ```
                def func(row_data):
                ```
        :return:
        """
        self.template_file = template_file
        self.sheet_name = sheet_name
        if isinstance(input_file, (str, unicode)):
            self.input_file = [input_file]
        elif isinstance(input_file, (tuple, list)):
            self.input_file = input_file
        else:
            raise ValueError("input_file parameter should be tuple or list, but {!r} found".format(type(input_file)))
        self.result = None
        self.callback = callback
        if use_merge:
            self.merge = Merge(keys=merge_keys, left_join=merge_left_join, verbose=merge_verbose)
        else:
            self.merge = False

        self.init()

        if self.callback:
            self.callback(self.result)

    def init(self):
        template = self.get_template()

        self.result = self.read(template)

    def get_template(self):
        wb = load_workbook(self.template_file)

        sheet = wb[self.sheet_name]
        t = ReadTemplate(sheet)
        return t

    def get_sheet(self):
        for f in self.input_file:
            if isinstance(f, (str, unicode)):
                w = load_workbook(f)
                if self.sheet_name not in w.sheetnames:
                    sheet_names = w.sheetnames
                else:
                    sheet_names = [self.sheet_name]
            elif isinstance(f, (tuple, list)):
                if len(f) <= 1:
                    raise ValueError("Filename {} should be followed sheetnames, "
                        "but only filename found".format(f[0]))
                w = load_workbook(f[0])
                if f[1] == '*':
                    sheet_names = w.sheetnames
                else:
                    sheet_names = f[1:]
            else:
                raise ValueError("input_file argument should be string list "
                                 "or tuple list, but {!r} found".format(self.input_file))

            #返回sheet对象
            for name in sheet_names:
                yield w[name]


    def read(self, template):
        result = []
        for sheet in self.get_sheet():
            r = template.get_data(sheet)
            if self.merge:
                self.merge.add(r)
                result = self.merge.result
            else:
                result.extend(r)
        return result

class Merge(object):
    def __init__(self, keys=None, left_join=True, verbose=False):
        """
        :param alist: 将要合并的数组,每个元素为一个字典
        :param keys: 指明字典的key,如果是多层,则为路径,值为list,如 ['key', 'key1/key2']
        :return:
        """
        self.result = []
        self.keys = keys or []
        self.left_join = left_join
        self.verbose = verbose

    def add(self, *alist):
        for a in alist:
            if self.result:
                self.result = self.merge_list(self.result, deepcopy(a))
            else:
                self.result = deepcopy(a)

    def get_compare_key(self, d, path):
        v = []
        for k in d.keys():
            if path:
                _k = path + '/' + k
            else:
                _k = k
            if _k in self.keys:
                v.append(d[k])
        if v:
            return tuple([_k] + v)
        else:
            return v

    def merge_list(self, list1, list2, path=''):
        objs = {}
        result = []
        for i in list1:
            _key = self.get_compare_key(i, path)
            if _key:
                objs[_key] = i
                result.append(i)
            else:
                if i not in result:
                    result.append(i)
        for i in list2:
            _key = self.get_compare_key(i, path)
            if _key:
                if _key not in objs:
                    if not self.left_join:
                        d = deepcopy(i)
                        result.append(d)
                        objs[_key] = d
                    #如果是left_join=True,以左则数组为准
                    else:
                        if self.verbose:
                            print '---- Path=', path, 'Skip=', i
                else:
                    self.merge_dict(objs[_key], i)
            else:
                #如果是第二层以下,则简单合并,否则进行字典合并
                if path:
                    if not i in result:
                        result.append(i)
                else:
                    self.merge_dict(result[0], i)
                # if i not in result:
                #     result.append(i)

        return result

    def merge_dict(self, d1, d2):
        for k, v in d1.items():
            if isinstance(v, list):
                d1[k] = self.merge_list(v, d2.get(k, []), path=k)
            elif isinstance(v, dict):
                d1[k] = self.merge_dict(v, d2.get(k, {}))
            else:
                d1[k] = d2.get(k, d1[k])

