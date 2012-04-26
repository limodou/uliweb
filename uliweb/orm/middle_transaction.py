from uliweb import Middleware
import threading
from uliweb.orm import Begin, Commit, Rollback

class TransactionMiddle(Middleware):
    ORDER = 100
    
    def __init__(self, application, settings):
        self.db = None
        self.settings = settings
        
    def process_request(self, request):
        from sqlalchemy.pool import NullPool
        from uliweb.orm import get_connection

        if self.settings.ORM.CONNECTION_TYPE == 'short':
            self.db = get_connection(self.settings.ORM.CONNECTION, poolclass=NullPool,
                **self.settings.ORM.CONNECTION_ARGS)
        Begin(create=True)

    def process_response(self, request, response):
        try:
            if self.settings.ORM.CONNECTION_TYPE == 'short' and self.db:
                self.db.dispose()
                self.db = None
            
            return response
        finally:
            Commit(close=True)
            
    def process_exception(self, request, exception):
        if self.settings.ORM.CONNECTION_TYPE == 'short' and self.db:
            self.db.dispose()
            self.db = None
            
        Rollback(close=True)
        