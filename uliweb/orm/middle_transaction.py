from uliweb import Middleware
from uliweb.orm import Begin, CommitAll, RollbackAll, get_connection

class TransactionMiddle(Middleware):
    ORDER = 80
    
    def __init__(self, application, settings):
        self.db = None
        self.settings = settings
        
    def process_request(self, request):
        Begin()

    def process_response(self, request, response):
        try:
            return response
        finally:
            CommitAll(close=True)
            if self.settings.ORM.CONNECTION_TYPE == 'short':
                db = get_connection()
                db.dispose()
                
            #add post_commit process
            if hasattr(response, 'post_commit') and response.post_commit:
                response.post_commit()
            
    def process_exception(self, request, exception):
        RollbackAll(close=True)
        if self.settings.ORM.CONNECTION_TYPE == 'short':
            db = get_connection()
            db.dispose()
        