# How to test it?
# easy_install nose
# cd test
# nosetests test_manage.py

import os

class TestMakeProject:
    def setup_method(self, test_makeproject):
        import shutil
        if os.path.exists('test'):
            shutil.rmtree('test', ignore_errors=True)
        print 'setup'
            
    def teardown_method(self, test_makeproject):
        import shutil
        if os.path.exists('test'):
            shutil.rmtree('test', ignore_errors=True)
        print 'teardown'

    def test_makeproject(self):
        from uliweb import manage

        manage.call('uliweb makeproject -y test')
        assert os.path.exists('test')
        
    def test_makeapp(self):
        from uliweb import manage
        
        manage.call('uliweb makeproject -y test')
        os.chdir('test')
        manage.call('uliweb makeapp Hello')
        os.chdir('..')
        assert os.path.exists('test/apps/Hello')
        
