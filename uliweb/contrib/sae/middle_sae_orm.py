from uliweb import settings
from uliweb import Middleware
from uliweb.orm import get_connection

class DBConnectionMiddle(Middleware):
    ORDER = 30
    
    def __init__(self, application, settings):
        self.db = None
        
    def process_request(self, request):
        from sqlalchemy.pool import NullPool
        self.db = get_connection(settings.ORM.CONNECTION, poolclass=NullPool,
            **settings.ORM.CONNECTION_ARGS)

    def process_response(self, request, response):
        self.db.dispose()
        self.db = None
        return response
        
    def process_exception(self, request, exception):
        self.db.dispose()
        self.db = None
