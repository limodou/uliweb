# How to test it?
# easy_install nose
# cd test
# nosetests test_manage.py

import os

class TestMakeProject:
    def setUp(self):
        import shutil
        if os.path.exists('test'):
            shutil.rmtree('test', ignore_errors=True)
            
    def tearDown(self):
        import shutil
        if os.path.exists('test'):
            shutil.rmtree('test', ignore_errors=True)

    def test_case(self):
        from uliweb import manage

        manage.make_project('test')
        assert os.path.exists('test')
        
class TestMakeApp:
   def tearDown(self):
       import shutil
       if os.path.exists('test'):
           shutil.rmtree('test', ignore_errors=True)

   def test_app(self):
        from uliweb import manage
        
        manage.make_app('test')
        assert os.path.exists('test')
        