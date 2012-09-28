#! /usr/bin/env python
#coding=utf-8
# This module is used to parse and create new style ini file. This
# new style ini file format should like a very simple python program
# but you can define section like normal ini file, for example:
#
#    [default]
#    key = value
#
# Then the result should be ini.default.key1 = value1
# Whole ini file will be parsed into a dict-like object, but you can access
# each section and key with '.', just like ini.section.key
# For value can be simple python data type, such as: tuple, list, dict, int
# float, string, etc. So it's very like a normal python file, but it's has
# some sections definition.

import sys, os
import re
import codecs
import StringIO
import locale
import copy
import tokenize
import token
from sorteddict import SortedDict

__all__ = ['SortedDict', 'Section', 'Ini', 'uni_prt']

try:
    set
except:
    from sets import Set as set

try:
    defaultencoding = locale.getdefaultlocale()[1]
except:
    defaultencoding = None

if not defaultencoding:
    defaultencoding = 'UTF-8'
try:
    codecs.lookup(defaultencoding)
except:
    defaultencoding = 'UTF-8'

r_encoding = re.compile(r'\s*coding\s*[=:]\s*([-\w.]+)')
__default_env__ = {}

def set_env(env=None):
    global __default_env__
    
    __default_env__.update(env or {})
    
def uni_prt(a, encoding='utf-8', beautiful=False, indent=0):
    escapechars = [("\\", "\\\\"), ("'", r"\'"), ('\"', r'\"'), ('\b', r'\b'),
        ('\t', r"\t"), ('\r', r"\r"), ('\n', r"\n")]
    s = []
    indent_char = ' '*4
    if isinstance(a, (list, tuple)):
        if isinstance(a, list):
            s.append(indent_char*indent + '[')
        else:
            s.append(indent_char*indent + '(')
        if beautiful:
            s.append('\n')
        for i, k in enumerate(a):
            if beautiful:
                ind = indent + 1
            else:
                ind = indent
            s.append(indent_char*ind + uni_prt(k, encoding, beautiful, indent+1))
            if i<len(a)-1:
                if beautiful:
                    s.append(',\n')
                else:
                    s.append(', ')
        if beautiful:
            s.append('\n')
        if isinstance(a, list):
            s.append(indent_char*indent + ']')
        else:
            if len(a) == 1:
                s.append(',')
            s.append(indent_char*indent + ')')
    elif isinstance(a, dict):
        s.append(indent_char*indent + '{')
        if beautiful:
            s.append('\n')
        for i, k in enumerate(a.items()):
            key, value = k
            if beautiful:
                ind = indent + 1
            else:
                ind = indent
            s.append('%s: %s' % (indent_char*ind + uni_prt(key, encoding, beautiful, indent+1), uni_prt(value, encoding, beautiful, indent+1)))
            if i<len(a.items())-1:
                if beautiful:
                    s.append(',\n')
                else:
                    s.append(', ')
        if beautiful:
            s.append('\n')
        s.append(indent_char*indent + '}')
    elif isinstance(a, str):
        t = a
        for i in escapechars:
            t = t.replace(i[0], i[1])
        s.append("'%s'" % t)
    elif isinstance(a, unicode):
        t = a
        for i in escapechars:
            t = t.replace(i[0], i[1])
        try:
            s.append("u'%s'" % t.encode(encoding))
        except:
            import traceback
            traceback.print_exc()
    else:
        s.append(str(a))
    return ''.join(s)

class Section(SortedDict):
    def __init__(self, name, comments=None, encoding=None):
        super(Section, self).__init__()
        self._name = name
        self.add_comment(comments=comments)
        self._field_comments = {}
        self._field_flag = {}
        self._encoding = encoding
            
    def add(self, key, value, comments=None, replace=False):
        self.__setitem__(key, value, replace)
        self._field_flag[key] = replace
        self.add_comment(key, comments)
        
    def __setitem__(self, key, value, replace=False):
        if not replace:
            v = self.get(key)
            #for mutable object, will merge them but not replace
            if isinstance(v, (list, dict)):
                if isinstance(v, list):
                    value = list(set(v + value))
                else:
                    v.update(value)
                    value = v
        super(Section, self).__setitem__(key, value)
        
    def add_comment(self, key=None, comments=None):
        comments = comments or []
        if not isinstance(comments, (tuple, list)):
            comments = [comments]
        if not key:
            self._comments = comments
        else:
            self._field_comments[key] = copy.copy(comments)
        
    def comment(self, key=None):
        if not key:
            return self._comments
        else:
            return self._field_comments.get(key, [])
    
    def del_comment(self, key=None):
        self.add_comment(key, None)
        
    def dumps(self, out):
        if self._comments:
            print >> out, '\n'.join(self._comments)
        print >> out, '[%s]' % self._name
        for f in self.keys():
            comments = self.comment(f)
            if comments:
                print >> out, '\n'.join(comments)
            if self._field_flag.get(f, False):
                op = ' <= '
            else:
                op = ' = '
            buf = f + op + uni_prt(self[f], self._encoding)
            if len(buf) > 79:
                buf = f + op + uni_prt(self[f], self._encoding, True)
            print >> out, buf
            
    def __delitem__(self, key):
        super(Section, self).__delitem__(key)
        self.del_comment(key)
        
    def __delattr__(self, key):
        try: 
            del self[key]
        except KeyError, k: 
            raise AttributeError, k
    
    def __str__(self):     
        buf = StringIO.StringIO()
        self.dumps(buf)
        return buf.getvalue()
    
class Ini(SortedDict):
    def __init__(self, inifile=None, commentchar='#', encoding='utf-8', env=None):
        super(Ini, self).__init__()
        self._inifile = inifile
#        self.value = value
        self._commentchar = commentchar
        self._encoding = 'utf-8'
        self._env = __default_env__.copy()
        self._env.update(env or {})
        
        if self._inifile:
            self.read(self._inifile)
        
    def set_filename(self, filename):
        self._inifile = filename
        
    def get_filename(self):
        return self._inifile
    
    filename = property(get_filename, set_filename)
    
    def read(self, fobj):
        encoding = None
        
        if isinstance(fobj, (str, unicode)):
            f = open(fobj, 'rb')
            text = f.read()
            f.close()
        else:
            text = fobj.read()
            
        text = text + '\n'
        begin = 0
        if text.startswith(codecs.BOM_UTF8):
            begin = 3
            encoding = 'UTF-8'
        elif text.startswith(codecs.BOM_UTF16):
            begin = 2
            encoding = 'UTF-16'
            
        if not encoding:
            try:
                unicode(text, 'UTF-8')
                encoding = 'UTF-8'
            except:
                encoding = defaultencoding
                
        self._encoding = encoding
        
        f = StringIO.StringIO(text)
        f.seek(begin)
        lineno = 0
        comments = []
        status = 'c'
        section = None
        while 1:
            lastpos = f.tell()
            line = f.readline()
            lineno += 1
            if not line:
                break
            line = line.strip()
            if line:
                if line.startswith(self._commentchar):
                    if lineno == 1: #first comment line
                        b = r_encoding.search(line[1:])
                        if b:
                            self._encoding = b.groups()[0]
                            continue
                    comments.append(line)
                elif line.startswith('[') and line.endswith(']'):
                    sec_name = line[1:-1].strip()
                    #process include notation
                    if sec_name.startswith('include:'):
                        _filename = sec_name[8:].strip()
                        _filename = os.path.abspath(_filename)
                        if os.path.exists(_filename):
                            old_encoding = self._encoding
                            self.read(_filename)
                            self._encoding = old_encoding
                        else:
                            import warnings
                            warnings.warn(Warning("Can't find the file [%s], so just skip it" % _filename), stacklevel=2)
                        continue
                    section = self.add(sec_name, comments)
                    comments = []
                elif '=' in line:
                    if section is None:
                        raise Exception, "No section found, please define it first in %s file" % self.filename

                    #if find <=, then it'll replace the old value for mutable variables
                    #because the default behavior will merge list and dict
                    pos = line.find('<=')
                    if pos != -1:
                        begin, end = pos, pos+2
                        replace_flag = True
                    else:
                        pos = line.find('=')
                        begin, end = pos, pos+1
                        replace_flag = False
                        
                    keyname = line[:begin].strip()
                    rest = line[end:].strip()
                    #if key= then value will be set ''
                    if rest == '':
                        v = None
                    else:
                        f.seek(lastpos+end)
                        try:
                            value = self.__read_line(f)
                        except Exception, e:
                            import traceback
                            traceback.print_exc()
                            raise Exception, "Parsing ini file error in line(%d): %s" % (lineno, line)
                        try:
                            txt = '#coding=%s\n%s' % (self._encoding, value)
                            v = eval(txt, self._env, section)
                        except Exception, e:
                            raise Exception, "Converting value (%s) error in line %d:%s" % (value, lineno, line)
                    section.add(keyname, v, comments, replace=replace_flag)
                    comments = []
            else:
                comments.append(line)
                
    def save(self, filename=None):
        if not filename:
            filename = self.filename
        if not filename:
            filename = sys.stdout
        if isinstance(filename, (str, unicode)):
            f = open(filename, 'wb')
            need_close = True
        else:
            f = filename
            need_close = False
        
        print >> f, '#coding=%s' % self._encoding
        for s in self.keys():
            section = self[s]
            section.dumps(f)

    def __read_line(self, f):
        g = tokenize.generate_tokens(f.readline)
        
        buf = []
        time = 0
        while 1:
            v = g.next()
            tokentype, t, start, end, line = v
            if tokentype == 54:
                continue
            if tokentype in (token.INDENT, token.DEDENT, tokenize.COMMENT):
                continue
            if tokentype == token.NEWLINE:
                return ''.join(buf)
            else:
                if t == '=' and time == 0:
                    time += 1
                    continue
                buf.append(t)
    
    def __setitem__(self, key, value):
        if key not in self:
            super(Ini, self).__setitem__(key, value)
            
    def update(self, value):
        for k, v in value.items():
            self.set_var(k, v)

    def add(self, sec_name, comments=None):
        if sec_name in self:
            section = self[sec_name]
        else:
            section = Section(sec_name, comments, self._encoding)
            self[sec_name] = section
        return section
    
    def __str__(self):     
        buf = StringIO.StringIO()
        self.save(buf)
        return buf.getvalue()
    
    def get_var(self, key, default=None):
        obj = self
        for i in key.split('/', 1):
            obj = obj.get(i)
            if obj is None:
                break
          
        if obj is None:
            return default
        return obj
    
    def set_var(self, key, value):
        s = key.split('/', 1)
        obj = self
        for i in s[:-1]:
            obj = obj.add(i)
        obj[s[-1]] = value
        
        return True
        
    def del_var(self, key):
        s = key.split('/', 1)
        obj = self
        for i in s[:-1]:
            obj = obj.get(i)
            if obj is None:
                return False
        
        if s[-1] in obj:
            del obj[s[-1]]
            flag = True
        else:
            flag = False
        
        return flag
