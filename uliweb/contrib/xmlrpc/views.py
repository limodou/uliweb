def _wrap_result(handler, result, request, response, env):
    return result

def xmlrpc():
    import uliweb.contrib.xmlrpc as rpc
    import xmlrpclib
    from werkzeug import Response
    from uliweb.utils.common import log
    from uliweb import application as app, response
    
    p, m = xmlrpclib.loads(request.data)
    try:
        f = rpc.__xmlrpc_functions__.get(m)
        if f:
            mod, handler_cls, handler = app.prepare_request(request, f)
            result = app.call_view(mod, handler_cls, handler, request, response, _wrap_result, args=p)
            xml = xmlrpclib.dumps((result,), methodresponse=1)
        else:
            xml = xmlrpclib.dumps(xmlrpclib.Fault(-32400, 'system error: Cannot find or call %s' % m), methodresponse=1)
            log.debug('xmlrpc error: Cannot find or call %s' % m)
    except Exception as e:
        xml = xmlrpclib.dumps(xmlrpclib.Fault(-32400, 'system error: %s' % e), methodresponse=1)
        log.exception('xmlrpc error')
    response = Response(xml, content_type='text/xml; charset=utf-8')
    return response