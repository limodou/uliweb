from uliweb import Middleware
from uliweb.utils.common import request_url
from logging import getLogger
from datetime import datetime

log = getLogger(__name__.rsplit('.')[0])


class RecorderrMiddle(Middleware):
    ORDER = 600

    def __init__(self, *args, **kwargs):
        self.access_datetime = datetime(1970, 1, 1)
        super(RecorderrMiddle, self).__init__(*args, **kwargs)

    def process_request(self, request):
        self.access_datetime = datetime.now()

    def process_response(self, request, response):
        from uliweb import settings, functions, json_dumps
        import base64
        
        begin_datetime = self.access_datetime
        end_datetime = datetime.now()
        # #if not debug status it'll quit
        # if not settings.get_var('GLOBAL/DEBUG'):
        #     return response
        
        S = functions.get_model('uliwebrecorderstatus')
        s = S.all().one()
        if not s or s.status == 'E':
            return response
        
        if settings.get_var('ULIWEBRECORDER/response_text'):
            try:
                text = response.data
            except Exception as e:
                text = str(e)
        else:
            text = ''
        
        #test if post_data need to convert base64
        if not request.content_type:
            post_data_is_text = True
        else:
            post_data_is_text = self.test_text(request.content_type)
        if not post_data_is_text:
            post_data = base64.encodestring(request.data)
        else:
            post_data = json_dumps(request.POST.to_dict())

        #test if response.data need to convert base64
        response_data_is_text = self.test_text(response.content_type)
        if not response_data_is_text:
            response_data = base64.encodestring(text)
        else:
            response_data = text

        R = functions.get_model('uliwebrecorder')
        if request.user:
            user_id = request.user.id
        else:
            user_id = None
        max_content_length = settings.get_var('ULIWEBRECORDER/max_content_length')
        if len(response_data) > max_content_length:
            msg = "Content length is great than %d so it will be omitted." % max_content_length
            log.info(msg)
            response_data = msg
            response_data_is_text = True
        recorder = R(method=request.method,
                     url=request_url(request),
                     post_data_is_text=post_data_is_text,
                     post_data=post_data,
                     user=user_id,
                     response_data=response_data,
                     response_data_is_text=response_data_is_text,
                     status_code=response.status_code,
                     begin_datetime=begin_datetime,
                     end_datetime=end_datetime,
                     time_used=(end_datetime-begin_datetime).total_seconds()
                     )
        recorder_type = settings.get_var('ULIWEBRECORDER/recorder_type')
        if recorder_type == 'db':
            recorder.save()
        elif recorder_type == 'mq':
            mq_name = settings.get_var('ULIWEBRECORDER/mq_name', default='uliweb_recorder_mq')
            redis = functions.get_redis()
            redis.lpush(mq_name, recorder.dump())
        elif recorder_type == 'stream':
            log.info(recorder.dump())
        return response
            
    def test_text(self, content_type):
        from uliweb.utils.common import match
        from uliweb import settings
        
        m = content_type.split(';', 1)[0]
        r = match(m, settings.get_var('ULIWEBRECORDER/text_content_types'))
        return r
