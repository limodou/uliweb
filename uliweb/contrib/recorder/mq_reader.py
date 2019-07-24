from logging import getLogger

import signal

from uliweb import settings
from uliweb.contrib.redis_cli import get_redis

log = getLogger(__name__)


def proc_signal(signum, frame):
    exit()


signal.signal(signal.SIGINT, proc_signal)
signal.signal(signal.SIGTERM, proc_signal)


def call(args, options, global_options):
    redis_client = get_redis()
    mq_config = settings.get_var('ULIWEBRECORDER/mq')
    mq_name = mq_config.get('name')
    log.info('reading from mq [%s]' % mq_name)

    while redis_client.llen(mq_name):
        s = redis_client.rpop(mq_name)
        log.info(s)
