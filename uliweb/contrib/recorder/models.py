from uliweb.orm import *

class UliwebRecorderStatus(Model):
    status = Field(CHAR, max_length=1, choices=[('S', 'start'), ('E', 'stop')], default='E')
    
class UliwebRecorder(Model):
    """
    Used to store the request info, and will be replay later to test.
    """
    method = Field(str, max_length=10)
    url = Field(TEXT)
    post_data = Field(TEXT)
    post_data_is_text = Field(bool)
    status_code = Field(int)
    response_data = Field(TEXT)
    response_data_is_text = Field(bool)
    user = Reference('user')
    begin_datetime = Field(datetime.datetime, auto_now_add=True, index=True)
    end_datetime = Field(datetime.datetime, auto_now=True)
