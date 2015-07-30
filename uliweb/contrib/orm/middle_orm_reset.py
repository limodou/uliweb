from uliweb import Middleware
from uliweb.orm import set_dispatch_send, set_echo

class ORMResetMiddle(Middleware):
    ORDER = 70
    
    def process_request(self, request):
        set_echo(False)
        set_dispatch_send(True)