from uliweb import Middleware
from uliweb.orm import begin_sql_monitor, close_sql_monitor

class SQLMonitorMiddle(Middleware):
    ORDER = 90
    
    def process_request(self, request):
        from uliweb import settings

        if 'sqlmonitor' in request.GET or settings.ORM.SQL_MONITOR:
            self.monitor = begin_sql_monitor(settings.ORM.get('SQL_MONITOR_LENGTH', 70), record_details=False)

    def process_response(self, request, response):
        from uliweb import settings
        
        if 'sqlmonitor' in request.GET or settings.ORM.SQL_MONITOR:
            self.monitor.print_(request.path)
            close_sql_monitor(self.monitor)
        return response
            
    def process_exception(self, request, exception):
        from uliweb import settings
        
        if 'sqlmonitor' in request.GET or settings.ORM.SQL_MONITOR:
            self.monitor.print_(request.path)
            close_sql_monitor(self.monitor)