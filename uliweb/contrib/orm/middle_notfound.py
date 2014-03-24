from uliweb import Middleware, error
from uliweb.orm import NotFound

class ORMNotfoundMiddle(Middleware):
    ORDER = 110
    
    def __init__(self, application, settings):
        pass
        
    def process_exception(self, request, exception):
        if isinstance(exception, NotFound):
            error("%s(%s) can't be found" % (exception.model.__name__, exception.id))
        