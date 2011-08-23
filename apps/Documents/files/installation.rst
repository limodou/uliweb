Installation
=================

:Author: Limodou <limodou@gmail.com>

.. contents:: 

Requirement
--------------

* Python 2.4+
* setuptools (There's a bug in version less than 0.6c8 which will cause an installation failure.)
* wsgiref (Required if you use Python 2.4. It's shipped with Python 2.5+.)
* PIL (If you want to process images, used by the form module and upload app)

.. note::
 
    You can install wsgiref via::

        easy_install wsgiref
    
Installation
---------------

#. easy_install Uliweb

#. Download Uliweb package from http://code.google.com/p/uliweb/downloads/list or
   get the source files from svn::

       svn checkout http://uliweb.googlecode.com/svn/trunk/ uliweb

#. In uliweb installation directory, run ``setup.py`` to install it::

       python setup.py develop
    
   This command will install a link of the current Uliweb directory to the Python 
   site-packages directory. , and you can find an entry in easy_install.pth.
   This command will also install a script named ``uliweb`` to Python/Scripts
   directory. Make sure that you have added the Python and Python/Scripts directories 
   to your systems search path(adding the new path to the PATH environment). Doing this allows you
   to run the uliweb scripts anywhere on te commandline.
    
   .. note::
    
       Why not use ``python setup.py install``? The ``uliweb`` script
       can't be installed correctly using this method, I will appreciate if someone can help with this issue.
    
#. After above steps, run ``uliweb`` command in command line and see the tutorials 
    to learn how to use ``uliweb`` for web application development.
