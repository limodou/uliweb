Database and ORM
=====================

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

Uliweb don't bind any ORM, but you can use dispatch, App to encapsulate your
own usage of database or ORM. But Uliweb indeed has its own ORM, and also provide
an App, so you can easily use it. But please remember, Uliweb ORM is not forced,
and if you don't like it, you don't need to use it at all. But I want to make it
suit for many simple tasks. And Uliweb ORM is based on SQLAlchemy, so you can also
use many features from SQLAlchemy.

ORM Configuration
---------------------

First, you should add ``uliweb.contrib.orm`` to ``INSTALLED_APPS`` in ``apps/settings.ini``.
Then, there are several parameters you can set to control the behavior of the ORM.

.. code::

    [ORM]
    DEBUG_LOG = False
    AUTO_CREATE = True
    CONNECTION = 'sqlite://'

The ``DEBUG_LOG`` is used to toggle SQLAlchemy log, if set to ``True``, when executing
SQL, the SQL statements will be output in log.

The ``AUTO_CREATE`` is used to enable ORM create tables automatically. If set it to
False, you should create table yourself.

The ``CONNECTION`` is used to set the connection string. Just follow the SQLAlchemy
format. (You can see http://www.sqlalchemy.org/docs/05/dbengine.html#create-engine-url-arguments)

The common format is::

    driver://username:password@host:port/database
    
There are some examples::

    #sqlite
    sqlite_db = create_engine('sqlite:////absolute/path/to/database.txt')
    sqlite_db = create_engine('sqlite:///d:/absolute/path/to/database.txt')
    sqlite_db = create_engine('sqlite:///relative/path/to/database.txt')
    sqlite_db = create_engine('sqlite://')  # in-memory database
    sqlite_db = create_engine('sqlite://:memory:')  # the same

    # postgresql
    pg_db = create_engine('postgres://scott:tiger@localhost/mydatabase')
    
    # mysql
    mysql_db = create_engine('mysql://scott:tiger@localhost/mydatabase')
    
    # oracle
    oracle_db = create_engine('oracle://scott:tiger@127.0.0.1:1521/sidname')
    
    # oracle via TNS name
    oracle_db = create_engine('oracle://scott:tiger@tnsname')
    
    # mssql using ODBC datasource names.  PyODBC is the default driver.
    mssql_db = create_engine('mssql://mydsn')
    mssql_db = create_engine('mssql://scott:tiger@mydsn')
    
    # firebird
    firebird_db = create_engine('firebird://scott:tiger@localhost/sometest.gdm')

And if you don't like to modify the apps/settings.ini manually, you can
also start development sever via::

    uliweb runadmin
    
Then in Build page of http://localhost:8000/admin to set the settings of ORM App.

Model Definition
-------------------

In common, you may create your model in models.py. First you should import from 
uliweb.orm, then create your own model and it should inherit from ``Model`` class.
Then add any fields you want to define. For example:

.. code:: python

    from uliweb.orm import *
    import datetime
    
    class Note(Model):
        username = Field(CHAR)
        message = Field(TEXT)
        homepage = Field(str, max_length=128)
        email = Field(str, max_length=128)
        datetime = Field(datetime.datetime, auto_now_add=True)

Table Name
~~~~~~~~~~~~~

By default, the table name will be the lower string of model class name, so Note
model's table name should be ``note``.

And if you want to set it to other table name, you can define a ``__tablename__`` in 
model class. For example:

.. code:: python

    class Note(Model):
    
        __tableame__ = 't_note'

Property Definition
~~~~~~~~~~~~~~~~~~~~~

Uliweb ORM define a model field as Property, but you can also use field concept, 
it's no problem. 

Uliweb ORM can define property of a model in two ways. One is very like GAE data
store, just ``*Property`` class. The other is just using Field() function.

Below are real properties defined in Uliewb ORM::

    'BlobProperty', 'BooleanProperty', 'DateProperty', 'DateTimeProperty',
    'TimeProperty', 'DecimalProperty', 'FloatProperty',
    'IntegerProperty', 'Property', 'StringProperty', 'CharProperty',
    'TextProperty', 'UnicodeProperty'

But you may think they are not easy to remember, so you can use the second way
to define a property. Just using ``Field()``.

For Field() function, it'll receive a Python date type or some special SQLAlchemy 
type, and convert it to a real Property class and then create an instance of it.

The mapping of Python data type and Property are::

    str:StringProperty,
    CHAR:CharProperty,
    unicode: UnicodeProperty,
    TEXT:TextProperty,
    BLOB:BlobProperty,
    int:IntegerProperty,
    float:FloatProperty,
    bool:BooleanProperty,
    datetime.datetime:DateTimeProperty,
    datetime.date:DateProperty,
    datetime.time:TimeProperty,
    decimal.Decimal:DecimalProperty,
    DECIMAL:DecimalProperty,
    
ID Property
~~~~~~~~~~~~~~

By default, Uliweb ORM will automatically create an ID property for you, and you
don't need to define it.

Relation Definition
------------------------

Operation
----------- 

Transacation
--------------

