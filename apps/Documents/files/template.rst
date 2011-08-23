Template
================

:Author: Limodou <limodou@gmail.com>

.. contents::
.. sectnum::

It seems that every web framework has a template system. Uliweb also has
one. The Template of Uliweb comes from web2py project originally. But I've
changed it a lot. So many places are same as web2py. Ok, let's see how
to use template in Uliweb.

Features
----------

* Very simple and easy to learn and use
* You can embed Python code in template
* Don't have to care about the indentation of Python code, just remember adding
  ``pass`` after the block is over, template will automatically reindent it
* Python code and HTML code can be mixed
* Support Template multiple layers inherit
* Provide some builtin functions
* Can inject new functions or variables to template runtime environ variable
* Template will be compiled to Python code then run

Syntax
--------

There is only one tag mark of template, that is ``{{}}``. And there are different
tags according the first word of the tag text. The first word of tag content
can be treated as the name of the tag, and if the name is not a reserved tag 
name, the content will be treated as common Python code. 

Reserved Tag Syntax
~~~~~~~~~~~~~~~~~~~~~

* ``{{extend parent_template_file}}`` 
    ``extend`` is used to derive a parent template.
    
    ``parent_template_file`` is the template filename, it can be a string or a 
    variable. So these are all valid usages::

        {{extend "base.html"}}
        {{extend parent}}

    For the second one, the ``parent`` can be passed from the outside or be calculated 
    from template.
    
* ``{{include template_file}}``
    ``include`` is used to inclulde other template into current one.
    
    ``template_file`` is the template filename, it can be a string or a variable
    just like ``extend`` usage.
    
* ``{{=variable}}``
    ``=`` is used to output HTML escaped value. So if there are something like: ``&``,
    ``<``, etc will be escaped to HTML entity.
    
    ``variable`` can be a real Python variable, value, function call or anything 
    can return a value. So these are all valid usages::
    
        {{= 123}}
        {{= a}}  #here a should be define in other place or pass from outside
        {{= function(arg)}}
        {{= obj}    #obj can be cast to a string
        
    .. note::
    
        If you don't want to escape the output, you can use ``xml()`` builtin
        function, just like this::
        
            {{xml(v)}}
            
* ``{{block name}}...{{end}}``
    ``block`` will define a block, and child template can replace it if there is
    a same name block definition, it'll replace the previous one. So you can
    define some blocks in parent template, and change the content of it in child
    template when you want. 
    
    * Uliweb template supports multiple block inherit, that
      means you can define multiple blocks in parent template, and redefine one
      or any number blocks you want to replace in child template.
    * Block can be nested. So you can define a block in a block, even in child 
      template. Only the latest defined block will be used for a same name block.
    
Embeding Python Code
~~~~~~~~~~~~~~~~~~~~~~

You can easily embed Python code between ``{{`` and ``}}``, just like this:

.. code:: python

    {{ import os }}
    
You can use almost all Python code in template, but I suggest that just keep
simple and relationship with representation code in template, otherwise your
template will become bloated and difficult to maintain.

If you want to use Python block statement, just like: if, def, while, etc, you
should add ``pass`` when the block is over. For example:

.. code:: python

    {{if user=='admin':}}
        <p>Welcome</p>
    {{else:}}
        <a href="/login">Login</a>
    {{pass}}
    
The last ``{{pass}}`` is very important. These are some points:

* Just common Python code, so don't forget the last ``:``
* After block is over or when you want to unindent, just add ``pass``
* Python code can mix with HTML code, and all HTML code between Python code
  will be directly outputed.
* Don't need to care about the indent, Uliweb template will automaticall
  reindent it according the block and ``pass``.
    
More examples:

.. code:: python

    {{ if user=='admin':
        out.write('<p>Welcome</p>', escape=False)
          else:
        out.write('<a href="/login">Login</a>', escape=False)
        pass
    }}
    
This will get the same result as above. Here ``out`` is also a built object you
can use directly.

Builtin Objects
~~~~~~~~~~~~~~~~~

There are several builtin objects you can use directly list below:

* ``xml()``
    It's a function, you can use it to unescape output a object if you don't want
    some special characters(just like: ``&``, ``<``, etc) be converted to HTML entities.
  
* ``out``
    It's a object, Uliweb template use it to output the template buffer. If you
    want to output unescape content you can use: ``out.write(v, escape=False)`` or
    ``out.noescape(v)``, the results are the same.
    
How to use it standalone
---------------------------

Uliweb template module is just a single file module, you can use it in your 
project if you want. You can simple import it. For example:

.. code:: python

    >>> import template
    >>> print template.template("Hello, {{=name}}", {'name':'Uliweb'})
    Hello, Uliweb
    
It provides several functions:

* ``template(text, vars=None, env=None, dirs=None, default_template=None)``

  ``text`` 
    is the template string you want to process.
  
  ``vars`` 
    is a dict data type, it's the variables you want to use in template
  
  ``env`` 
    is also a dict data type, template will be executed under this environment.
  
  ``dirs`` 
    is the directories list, Uliweb will find the real template file path 
    according this list when it needed. If you don't pass this parameter, 
    the defult value will be ``[.]``, it means current directory.
  
  ``default_template`` 
    will be also used in searching template file, if it's been set, if it can't
    find the extend template or include template, this value will be used.
    
  This function will return a string value, which is the result of template 
  executing.
  
* ``template_file(filename, vars=None, env=None, dirs=None, default_template=None)``

  Most parameters' meaning of this function are the same as ``template()``. The only different
  is the first parameter is ``filename``. It's a template filename. So this function
  is mainly used to process template file but not string.

* ``render_text(text, vars=None, env=None, dirs=None, default_template=None)``

  All the parameters' meaning are the same as ``template()``. This function will 
  return the translated Python code.

* ``render_file(filename, vars=None, env=None, dirs=None, default_template=None, use_temp=False)``

  ``use_temp``
    if set to True, then Uliweb template will store the translated Python code
    to a temporary file, and if you render the same template file again, and if
    you haven't change the original template file after last render time, Uliweb
    template will use the temporary file instead, but not the real template file
    and rerenders it again. So this will speed the process.
    
  Other parameters' meaning of this function are the same as ``template()`` and 
  ``template_file``.  

* ``use_tempdir(dir=None)``

  By default, Uliweb template will not automatically storing trnaslated Python code
  to temporary directory. So if you want to use this feature, you should call this
  function first. ``dir`` will be the temporary directory, if not set, default 
  directory will be ``tmp/templates_temp``. So if you use this feature, make sure
  you have the write permission of temporary directory. 

How to use template in Uliweb
------------------------------

There are several ways to use template.

Automatically Mapping
~~~~~~~~~~~~~~~~~~~~~~~

When you developing a view function, if the return value is a dict data type,
Uliweb will automatically find a matched template and use the returned value
to render it. By default, the matched template filename will be the view function
name pluses ``'.html'``. For example, if the view function is ``index`` the template
filename will be ``index.html``.

Providing in response 
~~~~~~~~~~~~~~~~~~~~~~~

You can also provide a template filename in ``response`` object, just like this::

    response.template = 'another.html'
    
So this will make Uliweb use the ``another.thml`` as the template filename.

Dealing it yourself
~~~~~~~~~~~~~~~~~~~~~~~

You can also use any template system in view function. Juse use them and get the 
result, then return it. If the return value is not a dict data type, Uliweb
will wrap it to a Response object. And in Uliweb view functions, you can use 
``application.template`` to access the template, for example::

    def some_view_func():
        response.write(application.template('show_document.html', locals()))
        return response

        
