from wheezy.http import HTTPRequest, HTTPResponse

class Request(HTTPRequest):

    def _get(self):
        return self.query
    GET = property(_get)

    def _post(self):
        return self.form
    POST = property(_post)
    # params = HTTPRequest.values

    def _files(self):
        return self.files
    FILES = property(_files)

class Response(HTTPResponse):
    def __call__(self, environ, start_response):
        return super(Response, self).__call__(start_response)

def make_request(environ, **kwargs):
    kwargs = kwargs or {}
    return Request(environ, 'utf8', kwargs)

def make_response(content='', **kwargs):
    kw = {}
    kw['content_type'] = kwargs.pop('content_type', 'text/html; charset=UTF-8')
    kw['encoding'] = kwargs.pop('encoding', 'utf8')
    response = Response(**kw)
    response.write(content)
    return response