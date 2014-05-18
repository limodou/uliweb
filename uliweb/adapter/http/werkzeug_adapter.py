#########################################################################
#  uliweb.adapter.werkzeug
#  will define:
#  Request, Response,
#########################################################################

from werkzeug import Request as OriginalRequest, Response as OriginalResponse

class Request(OriginalRequest):
    GET = OriginalRequest.args
    POST = OriginalRequest.form
    params = OriginalRequest.values
    FILES = OriginalRequest.files

class Response(OriginalResponse):
    def write(self, value):
        self.stream.write(value)

def make_request(environ, **kwargs):
    return Request(environ, **kwargs)

def make_response(content='', **kwargs):
    if 'content_type' not in kwargs:
        kwargs['content_type'] = 'text/html; charset=UTF-8'
    return Response(content, **kwargs)