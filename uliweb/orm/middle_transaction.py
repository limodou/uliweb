from uliweb.middleware import Middleware
import threading

class TransactionMiddle(Middleware):
    ORDER = 100
    
    def __init__(self, application, settings):
        from uliweb.orm import get_connection
        self.db = get_connection()
        
    def process_request(self, request):
        self.db.begin()

    def process_response(self, request, response):
        conn = self.db.contextual_connect()
        if conn.in_transaction():
            self.db.commit()
        conn.close()
        return response
            
    def process_exception(self, request, exception):
        conn = self.db.contextual_connect()
        if conn.in_transaction():
            self.db.rollback()
        conn.close()
        