URL映射
=============

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

Uliweb使用Werkzeug的Routing来进行URL的处理。当你使用manage.py的makeapp命令生成一个新
的App时，它会自动生成views.py文件，其中会自动从uliweb.core.SimpleFrame中导出expose
函数，它是一个decorator函数，用于修饰view函数。

通过expose可以将一个URL与一个view函数进行绑定，然后通过url_for(这是SimpleFrame提供的用
于反向生成URL的方法)来生成反向的URL。


expose说明
-----------

目前，Uliweb还不支持集中的URL配置，因此你需要在每个view方法前加上expose()来定义URL。

基本用法为：

#. 缺省映射

   .. code:: python

        @expose()
        def index(arg1, arg2):
            return {}
        
   当expose()不带任何参数时，将进行缺省的映射。即URL将为:

   ::

        /appname/view_function_name/<arg1>/<arg2>
    
   如果view函数没有参数，则为：

   ::

        /appname/view_function_name
    
#. 固定映射

   .. code:: python

        @expose('/index')
        def index():
            return {}
    
#. 参数处理

   当URL只有可变内容，可以配置为参数。一个参数的基本形式为：

   .. code:: python

        <convertor(arguments):name>
    
   其中convertor和arguments是可以缺省的。convertor类型目前可以设置为：int, float, 
   any, string, unicode, path等。不同的convertor需要不同的参数。详情请参见
   下面的converter说明。最简单的形式就是<name>了，它将匹配/到/间的内容。

   name为匹配后参数的名字，它需要与绑定的view方法中的参数名相匹配。

#. 其它参数

   expose函数允许在义时除了给出URL字符串以外再提供其它的参数，比如：

   defaults

        它用来定义针对view函数中的参数的缺省值，例如你可以定义：
        
        .. code:: python
        
            @expose('/all', defaults={'page': 1})
            @expose('/all/page/<int:page>')
            def show(page):
                return {}
                
        这样两个URL都指向相同的view函数，但由于show方法需要一个page参数，所以对于第一
        个/all来说，需要定义一个缺省值。
        
    build_only
    
        如果设置为True，将只用来生成URL，不用于匹配。目前Uliweb提供了静态文件的处理，
        但一旦你想通过象Apache这样的web server来提供服务的话，就不再需要Uliweb的静态
        文件服务了。但是有些文件的链接却是依赖于这个定义来反向生成的，因此为了不进行匹配，
        可以加上这个参数，这样在访问时不会进行匹配，但是在反向生成URL时还可以使用。
        
    关于参数更多的说明请参见werkzeug下的routing.py程序。
    
.. note::

    在非GAE环境下不需要导入，因为Uliewb已经将其放入__builtin__环境中，可以直接使用，但是
    在GAE环境下需要导入，GAE不允许注入。
    
    如果你使用makeapp来创建App目录，则在生成的views.py中已经加入了导入语句，因此可以直接
    使用。
    
url_for说明
---------------

url_for可以根据view方法的名字来反向生成URL。要注意，它需要一个字符串形式的view方法名，
格式为：

::

    url_for('appname.views_module_name.function_name', **kwargs)
    
其中kwargs是与view方法中的参数相对应的。例如你在Hello中定义了如下URL：

.. code:: python

    @expose('/index')
    def index():
        pass
        
然后在反向生成URL时可以使用：

.. code:: python

    url_for('Hello.views.index') #结果为'/index'
    
如果你在运行时希望可以动态适应App名字的变化，可以使用：

.. code:: python

    url_for('%s.views.index' % request.appname)
    
其中request是请求对象，它有一个appname的属性表示访问的App的名字。

.. note::

    目前在views方法和template中都是可以直接使用这个函数的，不需要导入。

convertor说明
--------------

* int

  基本形式为：

  ::

    <int:name>                      #简单形式
    <int(fixed_digits=4):name>      #带参数形式
    
  支持参数有：

  * fixed_digits 固定长度
  * min 最小值
  * max 最大值

* float

  基本形式为：

  ::

    <float:name>                    #简单形式
    <float(min=0.01):name>          #带参数形式
    
  支持参数有：

  * min 最小值
  * max 最大值

* string 和 unicode

  这两个其实是一样的。

  基本形式为：

  ::

    <string:name>
    <unicode(length=2):name>
    
  支持的参数有：

  * minlength 最小长度
  * maxlength 最大长度
  * length 定长

* path

  与string和unicode类型，但是没有任何参数。就是匹配从第一个不是 ``/`` 的字符到跟着的字
  符串或末尾之间的内容。基本形式为：

  ::

    <path:name>
    
  举例：

  ::

    '/static/<path:filename>'
    
  可以匹配：

  ::

    '/static/a.css'         -> filename='a.css'
    '/static/css/a.css'     -> filename='css/a.css'
    '/static/image/a.gif'   -> filename='image/a.gif'
    
* any

  基本形式为：

  ::

    <any(about, help, imprint, u"class"):name>

  将匹配任何一个字符串。

