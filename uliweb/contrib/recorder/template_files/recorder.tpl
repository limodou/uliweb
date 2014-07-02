
def test(c, log, counter):
    {{for row in rows:}}{{<< row}}
    {{pass}}

if __name__ == '__main__':
    import os
    from datetime import datetime
    from uliweb.utils.test import client, Counter

    c = client('.')
    print 'Current directory is %s' % os.getcwd()
    print
    
    #log = 'recorder_test_%s.log' % datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    log = True
    
    counter = Counter()
    test(c, log, counter)
    
    print
    print 'Total cases is %d, %d passed, %d failed' % (counter.total,
        counter.passed, counter.failed)