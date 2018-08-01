#coding=utf8

import logging

log = logging.getLogger(__name__)

def jsonql():
    from . import query
    from uliweb import json

    print request.data
    d = request.json()
    try:
        result = query(d)
        result['status'] = '200'
        result['message'] = 'Success'
    except Exception as e:
        log.exception(e)
        result = {}
        result['status'] = '500'
        result['message'] = 'Error'
    return json(result)
