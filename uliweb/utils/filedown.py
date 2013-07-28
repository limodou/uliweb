#coding=utf8

import os
from time import time, mktime
from datetime import datetime
from zlib import adler32
import mimetypes
from werkzeug.http import http_date, is_resource_modified
from werkzeug import Response, wrap_file
from werkzeug.exceptions import NotFound
import six
from six.moves.urllib.parse import quote

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
    from uliweb import request
    from uliweb.utils.common import safe_str

    from werkzeug.useragents import UserAgent
    
    agent = UserAgent(env)
    
    fname = safe_str(filename, 'utf8')
    if agent.browser == 'msie':
        result = 'filename=' + quote(fname)
    elif agent.browser == 'safari':
        result = 'filename=' + fname
    else:
        result = "filename*=UTF-8''" + quote(fname)
    return result

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
            raise Exception("x_header_name or x_filename can't be empty")
        headers.append((x_header_name, x_filename))
        return Response('', status=200, headers=headers,
            direct_passthrough=True)
    else:
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

