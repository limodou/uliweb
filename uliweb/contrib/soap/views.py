#coding=utf-8
from uliweb import expose, functions
import logging
from pysimplesoap.simplexml import TYPE_MAP

log = logging.getLogger('uliweb.app')

def _wrap_result(handler, result, request, response, env):
    return result

def exception_handler(e, response):
    log.exception(e)
    response.error = True
    
def _fix_soap_datatype(data):
    def _f(args):
        s = list(args)[:]
        for i, v in enumerate(args):
            if not isinstance(v, dict):
                #this should be a single type, .e.g [str]
                if type(v) in TYPE_MAP.keys():
                    s[i] = {TYPE_MAP[type(v)]:v}
                else:
                    raise Exception("Unsupport type %r" % v)
        return s
    
    if isinstance(data, (tuple, list)):
        return _f(data)
    elif isinstance(data, dict):
        d = data or {}
        for k, v in d.items():
            if isinstance(v, (tuple, list)):
                d[k] = _f(v)
        return d
    else:
        return data
    
__soap_dispatcher__ = None

class SimpleRule(object):
    pass

class SoapView(object):
    config = 'SOAP'
    
    def soap(self):
        from pysimplesoap.server import SoapDispatcher
        import uliweb.contrib.soap as soap
        from uliweb.utils.common import import_attr
        from uliweb import application as app, request, response, url_for
        from functools import partial
        
        global __soap_dispatcher__
        
        if not __soap_dispatcher__:
            location = "%s://%s%s" % (
                request.environ['wsgi.url_scheme'],
                request.environ['HTTP_HOST'],
                request.path)
            namespace = functions.get_var(self.config).get('namespace') or location
            documentation = functions.get_var(self.config).get('documentation')
            dispatcher = SoapDispatcher(
                name = functions.get_var(self.config).get('name'),
                location = location,
                action = '', # SOAPAction
                namespace = namespace,
                prefix=functions.get_var(self.config).get('prefix'),
                documentation = documentation,
                exception_handler = partial(exception_handler, response=response),
                ns = True)
            for name, (func, returns, args, doc) in soap.__soap_functions__.get(self.config, {}).items():
                if isinstance(func, (str, unicode)):
                    func = import_attr(func)
                dispatcher.register_function(name, func, returns, args, doc)
        else:
            dispatcher = __soap_dispatcher__
            
        if 'wsdl' in request.GET:
            # Return Web Service Description
            response.headers['Content-Type'] = 'text/xml'
            response.write(dispatcher.wsdl())
            return response
        elif request.method == 'POST':
            def _call(func, args):
                rule = SimpleRule()
                rule.endpoint = func
                mod, handler_cls, handler = app.prepare_request(request, rule)
                result = app.call_view(mod, handler_cls, handler, request, response, _wrap_result, kwargs=args)
                r = _fix_soap_datatype(result)
                return r
            # Process normal Soap Operation
            response.headers['Content-Type'] = 'text/xml'
            log.debug("---request message---")
            log.debug(request.data)
            result = dispatcher.dispatch(request.data, call_function=_call)
            log.debug("---response message---")
            log.debug(result)
            response.write(result)
            return response
