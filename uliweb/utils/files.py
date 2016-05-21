#coding=utf-8
import os
import sys
from common import log

def save_file(fname, fobj, replace=False, buffer_size=4096):
    assert hasattr(fobj, 'read'), "fobj parameter should be a file-like object"
    path = os.path.dirname(fname)
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception as e:
            log.exception(e)
            raise Exception("Can't create %s directory" % path)
    
    if not replace:
        ff, ext = os.path.splitext(fname)
        i = 1
        while os.path.exists(fname):
            fname = ff+'('+str(i)+')'+ext
            i += 1
        
    out = open(fname, 'wb')
    try:
        while 1:
            text = fobj.read(buffer_size)
            if text:
                out.write(text)
            else:
                break
        return os.path.basename(fname)
    finally:
        out.close()

def unicode_filename(filename, encoding=None):
    encoding = encoding or sys.getfilesystemencoding()
    if isinstance(filename, unicode):
        return filename
    else:
        return unicode(filename, encoding)
    
def encode_filename(filename, from_encoding='utf-8', to_encoding=None):
    """
    >>> print encode_filename('\xe4\xb8\xad\xe5\x9b\xbd.doc')
    \xd6\xd0\xb9\xfa.doc
    >>> f = unicode('\xe4\xb8\xad\xe5\x9b\xbd.doc', 'utf-8')
    >>> print encode_filename(f)
    \xd6\xd0\xb9\xfa.doc
    >>> print encode_filename(f.encode('gbk'), 'gbk')
    \xd6\xd0\xb9\xfa.doc
    >>> print encode_filename(f, 'gbk', 'utf-8')
    \xe4\xb8\xad\xe5\x9b\xbd.doc
    >>> print encode_filename('\xe4\xb8\xad\xe5\x9b\xbd.doc', 'utf-8', 'gbk')
    \xd6\xd0\xb9\xfa.doc
    
    """
    import sys
    to_encoding = to_encoding or sys.getfilesystemencoding()
    from_encoding = from_encoding or sys.getfilesystemencoding()
    if not isinstance(filename, unicode):
        try:
            f = unicode(filename, from_encoding)
        except UnicodeDecodeError:
            try:
                f = unicode(filename, 'utf-8')
            except UnicodeDecodeError:
                raise Exception, "Unknown encoding of the filename %s" % filename
        filename = f
    if to_encoding:
        return filename.encode(to_encoding)
    else:
        return filename

def str_filesize(size):
    """
    >>> print str_filesize(0)
    0
    >>> print str_filesize(1023) 
    1023
    >>> print str_filesize(1024)
    1K
    >>> print str_filesize(1024*2)
    2K
    >>> print str_filesize(1024**2-1)
    1023K
    >>> print str_filesize(1024**2)
    1M
    """
    import bisect
    
    d = [(1024-1,'K'), (1024**2-1,'M'), (1024**3-1,'G'), (1024**4-1,'T')]
    s = [x[0] for x in d]
    
    index = bisect.bisect_left(s, size) - 1
    if index == -1:
        return str(size)
    else:
        b, u = d[index]
    return str(size / (b+1)) + u
