#coding=utf8

import os
from time import time, mktime
from datetime import datetime
from zlib import adler32
import mimetypes
from werkzeug.http import http_date, is_resource_modified
from werkzeug import Response, wrap_file
from werkzeug.exceptions import NotFound

def _opener(filename):
    if not os.path.exists(filename):
        raise NotFound
    return (
        open(filename, 'rb'),
        datetime.utcfromtimestamp(os.path.getmtime(filename)),
        int(os.path.getsize(filename))
    )

def _generate_etag(mtime, file_size, real_filename):
    return 'wzsdm-%d-%s-%s' % (
        mktime(mtime.timetuple()),
        file_size,
        adler32(real_filename) & 0xffffffff
    )
    
def _get_download_filename(env, filename):
    from uliweb.utils.common import safe_str
    import urllib2
    from werkzeug.useragents import UserAgent
    
    agent = UserAgent(env)
    
    fname = safe_str(filename, 'utf8')
    if agent.browser == 'msie':
        result = 'filename=' + urllib2.quote(fname)
    elif agent.browser == 'safari':
        result = 'filename=' + fname
    else:
        result = "filename*=UTF-8''" + urllib2.quote(fname)
    return result

#copy from http://docs.webob.org/en/latest/file-example.html
class FileIterable(object):
    def __init__(self, filename, start=None, stop=None):
        self.filename = filename
        self.start = start
        self.stop = stop
    def __iter__(self):
        return FileIterator(self.filename, self.start, self.stop)
    def app_iter_range(self, start, stop):
        return self.__class__(self.filename, start, stop)

class FileIterator(object):
    chunk_size = 4096
    def __init__(self, filename, start, stop):
        self.filename = filename
        self.fileobj = open(self.filename, 'rb')
        if start:
            self.fileobj.seek(start)
        if stop is not None:
            self.length = stop - start
        else:
            self.length = None
    def __iter__(self):
        return self
    def next(self):
        if self.length is not None and self.length <= 0:
            raise StopIteration
        chunk = self.fileobj.read(self.chunk_size)
        if not chunk:
            raise StopIteration
        if self.length is not None:
            self.length -= len(chunk)
            if self.length < 0:
                # Chop off the extra:
                chunk = chunk[:self.length]
        return chunk
    __next__ = next # py3 compat

def filedown(environ, filename, cache=True, cache_timeout=None, 
    action=None, real_filename=None, x_sendfile=False,
    x_header_name=None, x_filename=None, fileobj=None,
    default_mimetype='application/octet-stream'):
    """
    @param filename: is used for display in download
    @param real_filename: if used for the real file location
    @param x_urlfile: is only used in x-sendfile, and be set to x-sendfile header
    @param fileobj: if provided, then returned as file content 
    @type fileobj: (fobj, mtime, size)
    
    filedown now support web server controlled download, you should set
    xsendfile=True, and add x_header, for example:
    
    nginx
        ('X-Accel-Redirect', '/path/to/local_url')
    apache
        ('X-Sendfile', '/path/to/local_url')
    """
    from werkzeug.http import parse_range_header
    
    guessed_type = mimetypes.guess_type(filename)
    mime_type = guessed_type[0] or default_mimetype
    real_filename = real_filename or filename
    
    #make common headers
    headers = []
    headers.append(('Content-Type', mime_type))
    d_filename = _get_download_filename(environ, os.path.basename(filename))
    if action == 'download':
        headers.append(('Content-Disposition', 'attachment; %s' % d_filename))
    elif action == 'inline':
        headers.append(('Content-Disposition', 'inline; %s' % d_filename))
    if x_sendfile:
        if not x_header_name or not x_filename:
            raise Exception, "x_header_name or x_filename can't be empty"
        headers.append((x_header_name, x_filename))
        return Response('', status=200, headers=headers,
            direct_passthrough=True)
    else:
        request = environ.get('werkzeug.request')
        if request:
            range = request.range
        else:
            range = parse_range_header(environ.get('HTTP_RANGE'))
        #when request range,only recognize "bytes" as range units
        if range!=None and range.units=="bytes":
            rbegin,rend = range.ranges[0]
            try:
                fsize = os.path.getsize(real_filename)
            except OSError,e:
                return Response("Not found",status=404)
            if (rbegin+1)<fsize:
                if rend == None:
                    rend = fsize-1
                headers.append(('Content-Length',str(rend-rbegin+1)))
                headers.append(('Content-Range','%s %d-%d/%d' %(range.units,rbegin, rend, fsize)))
                return Response(FileIterator(real_filename,rbegin,rend),
                    status=206, headers=headers, direct_passthrough=True)
        
        #process fileobj
        if fileobj:
            f, mtime, file_size = fileobj
        else:
            f, mtime, file_size = _opener(real_filename)
        headers.append(('Date', http_date()))
    
        if cache:
            etag = _generate_etag(mtime, file_size, real_filename)
            headers += [
                ('ETag', '"%s"' % etag),
            ]
            if cache_timeout:
                headers += [
                    ('Cache-Control', 'max-age=%d, public' % cache_timeout),
                    ('Expires', http_date(time() + cache_timeout))
                ]
            if not is_resource_modified(environ, etag, last_modified=mtime):
                f.close()
                return Response(status=304, headers=headers)
        else:
            headers.append(('Cache-Control', 'public'))
    

        headers.extend((
            ('Content-Length', str(file_size)),
            ('Last-Modified', http_date(mtime))
        ))
    
        return Response(wrap_file(environ, f), status=200, headers=headers,
            direct_passthrough=True)
