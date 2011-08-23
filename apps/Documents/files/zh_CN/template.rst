模板
=============

:作者: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

Uliweb目前内置的模板系统采用web2py的，所以语法与web2py的模板系统完全一样。在原基础上进
行了必要的修改。

特点
-------

* 简单，易学
* 可以嵌入Python代码
* 不用过分关心Python代码的缩近，只要注意块结束时加pass，模板会自动对缩近进行重排
* Python代码与HTML可以交叉使用
* 支持模板的继承
* 支持类django的block的功能(此功能由Uliweb扩展)
* 提供一些方便的内置方法
* 支持环境的扩展(可以扩展可以直接在模板中使用的对象和方法)
* 先编译成Python代码，然后再执行

基本语法
------------

Uliweb的模板的语法很简单，只有四种类型的标记：

* ``{{＝ result}}`` 这是用来输出的标记。其中result可以是变量也可以是一个函数调用，它会自动
  对输出的内容进行转义
* ``{{<< result}}`` 这是用来输出非转义的内容，与上面相反。
* ``{{ }}`` 只使用{{}}的话表示里面为Python代码，可以是任何的Python代码，如：import之类的。
  如果是块语句，需要在块结束时使用pass。
* ``{{extend template}}`` 其中template可以是字符串，如 ``"layout.html"`` 或变量。它表示从
  父模板继承。
* ``{{include template}}`` 包括其它的模板。如果template省略，表示是子模板插入的位置。一个
  父模板只能定义一个插入点。
* ``{{block blockname}}{{end}}`` 用于定义一个块。在子模板中，对于要覆盖的block需要进行定义，
  则生成的结果将用子模板中的block定义替换父模板的。

模板环境
-----------

Uliweb的模板在运行时也象view一样会运行在一个环境中，在这个环境中，有一些对象和方法是在
内置环境中定义的，也有一些是在Uliweb的框架环境中定义的对象或方法。内置的环境你无法扩展，
但是框架环境允许你扩展，方法很象view的扩展方式，如在任何一个有效的app的settings.py中
可以定义：

.. code:: python

    from uliweb.core.dispatch import bind

    @bind('prepare_view_env')
    def prepare_template_env(sender, env):
        from uliweb.utils.textconvert import text2html
        env['text2html'] = text2html
    
经过上面的处理，你就可以直接在模板中使用text2html这个方法了。

目前已经有一些缺省的对象和方法可以直接用在模板中，它们目前与view是一样的，因此你可以参考
`视图 <views>`_ 文档进行了解。

内置环境
----------

Uliweb的模板本身已经定义了一些方法可以直接使用。

* out对象 它可以用来输出信息，详见下面的说明。
* ``cycle(*args)`` 可以在给定的值中进行循环输出，每次返回一个。

out 对象
----------

out 对象是模板中内置的用来输出文本的对象。你可以在模板中直接使用它，但一般是不需要的。它
有以下的方法：

* write(text, escape=True) 输出文本。escape表示是否要进行转义。
* noescape(text) 输出不转义的文本。

编码
------

模板缺省是使用utf-8编码进行处理。如果你传入unicode字符串，将自动转为utf-8编码。如果不
是unicode，则不做处理。建议全部使用utf-8编码。

基本用法
----------

1. 简单地变量输出

.. code:: django

    {{= "hello"}}
    {{= title}}
    
如果使用了变量，则要么由view进行传入，要么在模板的其它地方进行定义，如：

.. code:: django

    {{title="hello"}}
    {{= title}}
    
2. HTML代码直接输出

.. code:: django

    {{<< html}}
    
3. Python代码示例

.. code:: python+django

    {{import os
    out.write("<h1>Hello</h1>")
    }}
    
4. 模板继承

父模板 (layout.html)

.. code:: python+django

    <html>
    <head>
    <title>Title</title>
    </head>
    <body>
    {{block main}}{{end}}
    </body>
    </html>
    
子模板 (index.html)

.. code:: python+django

    {{extend "layout.html"}}
    {{block main}}
    <p>This is child template.</p>
    {{end}}
    
5. 包括其它的模板

.. code:: python+django

    <html>
    <head>
    <title>Title</title>
    </head>
    <body>
    {{include "child.html"}}
    </body>
    </html>
    