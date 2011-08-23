全局环境
=============

:作者: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

Uliweb提供了必要的运行环境和运行对象，因此我称之为全局环境。

对象
--------

有一些全局性的对象可以方便地从 uliweb 中导入，如：

.. code:: python

    from uliweb import application, request, response, settings, Request, Response

application
~~~~~~~~~~~~~

它是用来记录整个Uliweb项目的运行实例，全局唯一。application是 ``uliweb.core.SimpleFrame.Dispatcher``
的实例，它有一些属性和方法可以让你使用，例如：

apps
    将列举出当前application实例所有有效的App名称。它是一个list，比如： ``['Hello', 'uliweb.contrib.staticfiles']``
    
apps_dir
    当前application的apps的目录。
    
template_dirs
    缺省为当前application所有有效的App的template搜索目录的集合。
    
get_file(filename, dir='static')
    从所有App下的相应的目录，缺省是从static目录下查找一个文件。并且会先在当前请求对应
    的App下先进行查找，如果没找到，则去其它的App下的相应目录进行查找。
    
template(filename, vars=None, env=None)
    渲染一个模板，会先从当前请求对应的App下先进行查找模板文件。vars是一个dict对象。env
    不提供的话会使用缺省的环境。如果想向模板中注入其它的对象，但不是以vars方式提供，不用
    直接修改env，而是通过dispatch功能，绑定： ``prepare_view_env`` 主题就可以了。
    
    它会返回渲染后的结果，是字符串。
    
render(filename, vars, env=None)
    它很象template，不过它是直接返回一个Response对象，而不是字符串。
    
Request
~~~~~~~~~~~~

而这里的Request类是基于werkzeug的Request来派生的，区别在于：

    增加了一些兼容性的内容。原来的werkzeug的Request是没有象GET, POST, params, FILES这
    样的属性的，它们分别是：args, form, values, files，为了与其它的Request类兼容，我
    添加了GET, POST, params, FILES属性。
    
Response
~~~~~~~~~~~~

它也对werkzeug提供的Response进行了派生，区别在于：

    添加了一个write方法。而原werkzeug的Response类有一个stream属性，它有write方法。经过
    扩展，可以直接使用write方法，会更方便一些。

request
~~~~~~~~~~~~

request 是上面 Request 类的实例的一个代理对象，并不是一个真正的 Request 对象，
response 也是。但是你可以把它当成真正的 Request 和 Response 一样来使用。那么为什
么要这样，为了方便。真正的 Request 和 Response 对象会在收到一个请求时被创建
，然后存放到 local 中，这样不同的线程将有不同实例。为了方便使用，采用代理方式，
这样用户就不用直接调用 local.reuqest 和 local.response ，而是简单使用 request 和
response 就可以根据不同的线程使用不同的对象了。

.. note::

    request和response是有生存周期的，就是在收到请求时创建，在返回后失效。因此在使用它们
    时，要确保你是在它们的生存周期中进行使用的。

在讲View的环境时提到过：写一个view方法时有一些对象可以认为是全局的，其中就包括request和
response，但是这两个对象与其它的不同就是因为它是线程相关并且有生存周期的，其它的则是全局唯
一，并且生存周期是整个运行实例的生存周期。这样，在非view函数中想要使用request和response
对象，一种方式就是在view中传入，但是可能有些麻烦，另一种方式就是通过uliweb来导入，这样就
很方便。

request在行为上和Request一样。
    
response
~~~~~~~~~~~~

和request一样是一个代理对象。
    
settings
~~~~~~~~~~~

配置信息对象，这个没什么好说的。

方法
--------

如：

.. code:: python

    from uliweb import (redirect, json, POST, GET, post_view, 
        pre_view, url_for, expose, get_app_dir, get_apps
        )

redirect
~~~~~~~~~~

.. code:: python

    def redirect(location, code=302):
    
返回一个Response对象，用于实现URL跳转.

json
~~~~~~~~

.. code:: python

    def json(data):
    
将一个data处理成json格式，并返回一个Response对象。

expose
~~~~~~~~~

详见 `URL映射 <url_mapping>`_

POST
~~~~~

和expose一样，不过限定访问方法为 POST。

GET
~~~~~

和expose一样，不过限定访问方法为 GET。

url_for
~~~~~~~~~

.. code:: python

    def url_for(endpoint, **values):

根据endpoint可以反向获得URL，endpoint可以是字符串格式，如: ``Hello.view.index`` ， 也可以
是真正的函数对象。

get_app_dir
~~~~~~~~~~~~~~

.. code:: python

    def get_app_dir(app):

根据一个app名字取得它对应的目录。

get_apps
~~~~~~~~~~~

.. code:: python

    def get_apps(apps_dir, include_apps=None):
    
根据一个apps目录，分析出所有可用的App的名字列表。