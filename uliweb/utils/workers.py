# This module used to create multi worker processes shipped with a manager
# And it's only a framework which will manager the process create, quit, etc.
# It'll be used in daemon.

from __future__ import print_function, absolute_import

__all__ = ['Worker', 'Manager', 'make_log']
__version__ = '0.1'

import os
import sys
import time
import signal
import logging
from .process import pid_exists, wait_pid

default_log = logging.getLogger(__name__)

is_exit = False

class TimeoutException(Exception):
    pass

class Timeout():
    """Timeout class using ALARM signal."""

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):
        raise TimeoutException("Timeout {}s".format(self.sec))

def get_memory(pid):
    # return the memory usage in MB, psutil should be 4.0 version
    from psutil import Process, __version__

    # if __version__ < '4.0.0':
    #     raise Exception('psutil module should be 4.0.0 version at least.')

    if pid_exists(pid):
        process = Process(pid)
        # mem = process.memory_full_info().uss / float(1024*1024)
        mem = process.memory_info().rss / float(1024*1024)
        return mem
    return 0

FORMAT = "[%(levelname)s - %(asctime)s - %(filename)s:%(lineno)s] - %(message)s"

def make_log(log, log_filename, format=FORMAT, datafmt=None, max_bytes=1024*1024*50,
             backup_count=5):
    import logging.handlers

    if isinstance(log, (str, unicode)):
        log = logging.getLogger(log)

    handler = logging.handlers.RotatingFileHandler(
        log_filename, maxBytes=max_bytes, backupCount=backup_count)
    fmt = logging.Formatter(format, datafmt)
    handler.setFormatter(fmt)
    log.addHandler(handler)
    return log

class Worker(object):
    _id = 1

    def __init__(self, log=None,
                 max_requests=None,
                 soft_memory_limit=200, #memory limit MB
                 hard_memory_limit=300, #memory limit MB
                 timeout=None,
                 check_point=None,
                 name=None,
                 args=None, kwargs=None):
        self.log = log or default_log
        self.max_requests = max_requests or sys.maxint
        self.soft_memory_limit = soft_memory_limit
        self.hard_memory_limit = hard_memory_limit
        self.timeout = timeout
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.is_exit = None
        self.count = 0
        self.check_point = check_point
        self.name = "%s-%d" % ((name or 'Process'), self._id)
        self.__class__._id += 1

    def start(self):
        self.pid = os.getpid()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGUSR1, self.signal_handler_usr1)
        signal.signal(signal.SIGUSR2, self.signal_handler_usr2)

        self.init()
        try:
            self._run()
            self.on_finished()
        except Exception as e:
            self.log.exception(e)
            self.on_exception(e)

        self.after_run()

    def init(self):
        self.log.info('%s %d created' % (self.name, self.pid))

    def run(self):
        self.log.info('%s %d running' % (self.name, self.pid))
        time.sleep(1)
        return True

    def on_exception(self, e):
        pass

    def on_finished(self):
        pass

    def _run(self):
        while (not self.max_requests or
                   (self.max_requests and self.count <= self.max_requests)) and \
                not self.is_exit:
            try:
                if self.timeout:
                    with Timeout(self.timeout):
                        ret = self.run()
                else:
                    ret = self.run()
            except TimeoutException as e:
                self.log.info('Time out')
            finally:
                # !important
                # count shoud be calculated by child class
                # self.count += 1
                if self.check_point:
                    time.sleep(self.check_point)

    def after_run(self):
        if self.is_exit == 'signal':
            self.log.info('%s %d cancelled by signal.' % (self.name, self.pid))
        elif self.is_exit == 'timeout':
            self.log.info("%s %d cancelled by reaching timeout %ds" %
                          (self.name, self.pid, self.timeout))
        elif self.is_exit == 'quit':
            self.log.info("%s %d quit!" % (self.name, self.pid))
        elif self.max_requests and self.count>self.max_requests:
            self.log.info('%s %d cancelled by reaching max requests count [%d]' % (
                self.name, self.pid, self.max_requests))
        else:
            self.log.info('%s %d cancelled by exception occorred' % (
                self.name, self.pid))

    def signal_handler(self, signum, frame):
        self.is_exit = 'signal'
        self.log.info ("%s %d received a signal %d" % (self.name, self.pid, signum))
        os._exit(0)

    def signal_handler_usr1(self, signum, frame):
        """hard memory limit"""
        self.is_exit = 'signal'
        self.log.info ("%s %d received a signal %d" % (self.name, self.pid, signum))
        os._exit(0)

    def signal_handler_usr2(self, signum, frame):
        """soft memory limit"""
        self.is_exit = 'signal'
        self.log.info ("%s %d received a signal %d" % (self.name, self.pid, signum))
        os._exit(0)

    def reached_soft_memory_limit(self, mem):
        if self.soft_memory_limit and mem >= self.soft_memory_limit:
            return True
        else:
            return False

    def reached_hard_memory_limit(self, mem):
        if self.hard_memory_limit and mem >= self.hard_memory_limit:
            return True
        else:
            return False

class Manager(object):
    def __init__(self, workers, log=None, check_point=10,
                 title='Workers Daemon', wait_time=3, daemon=False):
        """
        :param workers: a list of workers
        :param log: log object
        :param check_point: time interval to check sub process status
        :return:
        """
        if not workers:
            log.info('No workers need to run.')
            sys.exit(0)

        self.log = log or logging.getLogger(__name__)
        self.workers = workers
        #reset log
        for w in self.workers:
            w.log = self.log
        self.is_exit = False
        self.check_point = check_point
        self.title = title
        self.wait_time = wait_time
        self.daemon = daemon

    def init(self):
        _len = len(self.title)
        self.log.info('='*_len)
        self.log.info('%s' % self.title)
        self.log.info('='*_len)
        self.log.info('Daemon process %d' % self.pid)
        self.log.info('Check point %ds' % self.check_point)

    def start(self):
        self.pid = os.getpid()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.init()
        self.run()
        self.after_run()

    def join(self):
        for child in self.pids.values():
            if pid_exists(child):
                wait_pid(child)

    def run(self):
        self.pids = pids = {}

        while 1:
            for i, worker in enumerate(self.workers):
                pid = pids.get(i)
                create = False
                if not pid:
                    create = True
                else:
                    #reap child process !important
                    os.waitpid(pid, os.WNOHANG)
                    if not pid_exists(pid):
                        self.log.info('%s %d is not existed any more.' % (worker.name, pid))
                        create = True

                if create:
                    pid = os.fork()
                    #main
                    if pid:
                        pids[i] = pid
                    #child
                    else:
                        try:
                            worker.start()
                        except Exception as e:
                            self.log.exception(e)
                        sys.exit(0)
                else:
                    try:
                        mem = get_memory(pid)
                        if worker.reached_hard_memory_limit(mem):
                            self.kill_child(pid, signal.SIGUSR1)
                            self.log.info('%s %d memory is %dM reaches hard memory limit %dM will be killed.' % (
                                worker.name, pid, mem, worker.hard_memory_limit))
                        elif worker.reached_soft_memory_limit(mem):
                            self.kill_child(pid, signal.SIGUSR2)
                            self.log.info('%s %d memory is %dM reaches soft memory limit %dM will be cannelled.' % (
                                worker.name, pid, mem, worker.soft_memory_limit))
                    except Exception as e:
                        self.log.info(e)

            if not self.daemon:
                return

            time.sleep(self.check_point)


    def after_run(self):
        pass

    def kill_child(self, pid, sig=signal.SIGTERM):
        if pid_exists(pid):
            os.kill(pid, sig)
            wait_pid(pid, 3, lambda x:os.kill(x, signal.SIGKILL))
            wait_pid(pid, 2)
        #remove pid
        self.pids.pop(pid, None)

    def signal_handler(self, signum, frame):
        self.log.info ("Process %d received a signal %d" % (self.pid, signum))
        for child in self.pids.values():
            self.kill_child(child)
        sys.exit(0)


