
import os
from datetime import datetime

from uliweb.utils.test import client
c = client('.')
print 'Current directory is %s' % os.getcwd()
print

log = 'recorder_test_%s.log' % datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

{{for row in rows:}}{{<< row}}
{{pass}}