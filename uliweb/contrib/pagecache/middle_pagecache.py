from uliweb import Middleware
from werkzeug.http import http_date
from time import time

class PageCacheMiddle(Middleware):
    def compute_etag(self, data):
        import hashlib
        
        hasher = hashlib.sha1()
        hasher.update(data)
        return '"%s"' % hasher.hexdigest()
    
    def process_response(self, request, response):
        from uliweb import settings
        
        if (hasattr(response, 'etag') and getattr(response, 'etag', False)) or \
            (not hasattr(response, 'etag') and settings.PAGECACHE.get('etag', False)):
            if (response.status_code == 200 and
                request.method in ("GET", "HEAD") and "ETag" not in response.headers):
                etag = self.compute_etag(response.data)
                if etag is not None:
                    inm = request.headers.get("If-None-Match")
                    if inm and inm.find(etag) != -1:
                        response.data = ''
                        response.status_code = 304
                        response.headers["Content-Length"] = 0
                    else:
                        t = time()
                        response.headers["ETag"] = etag
                        response.headers['Cache-Control'] = 'max-age=%d, public' % settings.PAGECACHE.cache_timeout
                        response.headers['Expires'] = http_date(t + settings.PAGECACHE.cache_timeout)
                        response.headers['Last-Modified'] = http_date(t)
                        
        return response