class Middleware(object):
    ORDER = 500
    
    def __init__(self, application, settings):
        self.application = application
        self.settings = settings
        
#    def process_request(self, request):
#        pass
#    
#    def process_response(self, request, response):
#        pass
#    
#    def process_exception(self, request, exception):
#        pass