Form
================

:Author: Limodou <limodou@gmail.com>

.. contents:: 
.. sectnum::

Form creation and processing is a big problem in web development. Uliweb provides
its own form processing module, but it is not bound for use by default just in 
case you intend to use another form processing module. This 
module is named ``form`` and can be found in the ``uliweb`` directory. It is 
basically a normal Python module, and can, as such, be imported as one for use.

The features of the form module are:

* Ease of use. Just define it like a simple class and instanciate it for use.
* Easy HTML code generation. HTML code can be generated directly from Field or Form objects
* Support for custom HTML layout processes.
* Can validate the submitted data and convert them into Python data types
* Support user defined validators
* Support for file uploads and management.

The Form Class
----------------

To get started, define a Form class first, as follows:

.. code:: python

    from uliweb.form import *

    class Form1(Form):
        title = TextField(label='Title:', required=True, help_string='Title help string')
        content = TextAreaField(label='Content:')

You can see, you should inherit from ``Form`` class, and you can define field directly
in Form class, just like define class attributes.

Then you could create Form object, just like:

.. code:: python

    f = Form1()
    
When creating Form instance, there are some parameters you can set:

    action
        It's the ``action`` attribute of <form> tag, if not set it, it'll be ``""``.
        
    method
        It's the ``method`` attribute of <form> tag, if not set it, it'll be ``post``.
        
    buttons
        It'll be used to create button lines of a form, like submit and reset button.
        If you not set it, default will be submit and reset buttons. The HTML code
        will be:
        
        .. code:: html
        
            <input type="submit" value="Submit"></input>
            <input type="reset" value="Reset"></input>
            
        If you want other buttons, you can provide any HTML code in ``buttons`` 
        parameter, Form will use it to create buttons.

    validators
        User can write Form level validators, it should be a list of validators.
        More details about validator you can see *Validator* section below.
        
    html_attrs
        Other attributes you can set to form tag.
        
    data
        Data you want to set. It should be a dict, each key will be the attribute
        name. If you set it, it'll be replace with default value of matched field.
        You don't need to set it in initialization, you can use Form.binding() 
        or when you call Form.validate() to validate the submit data, the errors 
        will be automatically bound.
        
    errors
        Error message of each field or the global error. It's a dict too. And if
        the key is ``'_'`` it means it's global error. You don't need to set it in 
        initialization, you can use Form.binding() or when you call Form.validate()
        to validate the submit data, the errors will be automatically bound.
        
    idtype
        idtype is used to indicate how to create ``id`` attribute. Default is ``'name'``,
        that means when creating HTML code for a field, it'll use the field name
        as the ``id`` value, the format will be ``field_<fieldname>``. If it's ``None``,
        the created HTML code will not has ``id`` attribute at all. And if it's other
        value the id format will be ``field_<no>``, each field will have a unique
        id number value when creating the instance.
        
Defining a Form
------------------

You can define any field as you want in a Form class, just define it in Form class
just like abvoe example. More details about available fields you can see *Bultin
Fields* section.

Beside defining fields in a Form class, you can also define validators for fields
or whole Form. For example:

.. code:: python

    from uliweb.form import *

    class F(Form):
        user_name = StringField(required=True)
        password = PasswordField(required=True)
        enter_password_again = PasswordField(required=True)
        
        def validate_user_name(self, value):
            if value != 'limodou':
                raise ValidationError, 'Username should be limodou'
            
        def form_validate(self, all_values):
            if all_values.password != all_values.enter_password_again:
                raise ValidationError, 'Passwords are not matched'

This example demenstrates how to define a validateor for ``user_name`` field in
the ``F`` form. You can define a function which name is like ``validate_<field_name>``.
And how to define a whole Form level validator, just define a function which
name is ``form_validate``.

Form Layout
--------------

Form class supports layout feature. A layout can be used to create real
HTML code. There are two layouts: TableLayout and CSSLayout already defined
in Form module. So you can use them directly. Default is TableLayout. And if you
want to change it, just define a ``layout_class`` attribute in Form class. 
For example:

.. code:: python

    from uliweb.form import *

    class F(Form):
        layout_class = CSSLayout
        
        title = StringField(label='Title:', required=True, help_string="This is a help string")
        date = DateField(label='Date:', name='adate', required=True)

Outputing HTML Code
----------------------

For simple cases, you may want to output Form HTML code with empty value. For 
example, below is view function:

.. code:: python

    from uliweb.form import *

    @expose('/form_test')
    def form_test():
        class F(Form):
            user_name = StringField(required=True)
            password = PasswordField(required=True)
            enter_password_again = PasswordField(required=True)

        f = F()
        return {'form':f}
        
So after you create the instance of ``F``, you can return a dict to template. And
the template is:

::

    {{ if '_' in form.errors: }}
    <h2>Error:{{=form.errors._}}</h2>
    {{pass}}
    {{<< form}}

For first 3 lines, they are the form level error display process. And ``{<< form}}``
is: outputing the form object without escaping, so characters like ``<`` etc. will
not be converted to ``&lt;``. That's exactly what we want.

If you want the form have initial values, you have two ways. One you can pass the
``data`` and ``errors`` (if existing) parameters to Form initialization function. For
example:

.. code:: python

    from uliweb.form import *

    class F(Form):
        user_name = StringField(required=True)
        password = PasswordField(required=True)
        enter_password_again = PasswordField(required=True)
    
    d = {'user_name':'limodou'}
    f = F(data=d)
    
Or you can use Form.bind() function. For example:

.. code:: python

    f = F()
    f.bind(data=d)
    
.. note::

    The ``data`` should be a dict, and the values are matched with the Fields date
    type.

You can also output Form HTML code with ``f.html()`` method, it the same as ``str(f)``.
Here ``f`` is the instance of a defined Form.

Because f.html() will output a whole Form HTML code, but sometimes you may want
to create Form HTML code yourself, and you can do it in template. form module also
provides funnctions to help you to do that. For example:

::

    {{<<form.form_begin}}
    <dl>
    <dt>{{<<form.title.label}}</dt>
    <dd>{{<<form.title}} {{<<form.f.title.error}} {{<<form.f.title.help_string}}</dd>
    <dt>{{<<form.title.label}}</dt>
    <dd>{{<<form.title}}</dd>
    <dt>{{<<form.date.label}}</dt>
    <dd>{{<<form.date}}</dd>
    
    </dl>
    {{<<form.buttons}}
    {{<<form.form_end}}

You can see, Form has provides: ``form.form_begin``, ``form.form.buttons``, ``form.form_end``,
and ``form.<field>.lable``, ``form.<field>``, ``form.<field>.error``, ``formm.<field>.help_string``
methods or properties to create a Form in a template.

.. note::

    If you've already validated submitted data, the data or errors will be bound
    to the form instance, so when you re-render the form instance again, just lik
    ``return {'form':f}`` and ``{{<< form}}``, it'll output the data and errors to 
    HTML code.

Validating Submitted Data
-----------------------------

When you defining a Form, you may want to validate the value. And you've seen 
how to define validator functions in a Form. So when user submitting the data,
how to validate them and what's the next step after validating?

You can use Form.validate() to validate the submmited data. For example:

.. code:: python

    from uliweb.form import *
    
    class F(Form):
        user_name = StringField(required=True)
        password = PasswordField(required=True)
        enter_password_again = PasswordField(required=True)
    
    f = F()
    if f.validate(request.params):
        ...
    else:
        return {'form':f}
        
Above example demonstrates how to validate the submitted data. You should pass
``request.GET`` or ``request.POST`` or ``request.params`` or ``request.FILES`` to Form.validate() 
function. Or you can also pass multiple vars to Form.validate(), just like:

.. code:: python

    f.validate(request.POST, request.FILES)

.. note::

    Here the data passed to Form.validate() should be a dict-like object, and if 
    you define ``multiple`` parameter in one field definition, the data should 
    support getall() method or getlist() method.
    
If Form.validate() validate the submitted data ok, it'll return ``True``. Or it'll return
``False``. If the validatation result is ``True``, the submitted data will be converted to
Python data type, and be bound to the Form instance. You can use ``Form.data`` and 
``Form.errors`` to get the data and errors. They are dict data type. You can also
use ``Form.<field>.data`` and ``Form.<field>.error`` to get one field data and error.

So after validating the data, you can use ``form.data`` or ``form.<field>.data`` to do 
more process.

Field Definition
-------------------

The basic field class definition will be:

.. code:: python

    Form.BaseField(label='', default=None, required=False, validators=None, 
        name='', html_attrs=None, help_string='', build=None, datatype=None, 
        multiple=False, idtype=None, **kwargs)
        
Let's explain these parameters one by one:

    label
        Will be used to display a ``<label>label</label>`` tag. If it's empty,
        Uliweb form will use the field name, and it'll convert a field name to
        camel case format, and if ``'_'`` is in field name, it'll be converted to 
        space. So ``user_name`` will be converted to ``User Name``.
        
    default
        Default value of a field. There are many usages of defult parameter.
        When you render the field to HTML code, if the field data is not existed,
        default value will be used. Or when you validating submitted data, and 
        the feild is not required, and there is no matched submitted data, default
        value will be used. default value for DateField and TimeField has other
        usage, you'll find it at DateField description.
        
        Different fields have differnt default value, you should validate documentan
        carefully.
        
    required
        Indicate whether a field is must existed. Default is False. If it's ``True``,
        you must enter value to the field, but not empty value. If it's ``False``,
        you don't need to enter the field.
        
    validators
        It's a validators list. If you want to validate whether the submitted
        data is correct, you can define your validator functions or just use built-in
        validator functions, and pass a validators list to it. More details please
        read *Validator* section.
        
    name
        The name of the field. By default, you don't need to define it, because
        when you define a field in a form, Uliweb form will assign field name to
        field instance. But you can still pass ``name`` parameter to a field. That
        will result: the form will use field name to access the data, and HTML
        code will use ``name`` to access the HTML data. For example:
        
        .. code:: python
        
            from uliweb.form import *
            
            class F(Form):
                user_name = StringField(name='username')
                
        So you can see the you defined a field with ``user_name``, but it's really
        name is ``username``.
        
    help_string
        Just a help string of the field. And Layout class can use it to display
        a hint message.
        
    build
        Every field has a defult HTML code build class, but you can change default
        build class by passing this parameter. But you seldom to use it.
        
    datatype
        Every field has a default Python data type, and it'll be used when validating
        the submitted data, it'll convert the HTML code to defult Python data type.
        But you can change the default data type by passing this parameter.
        
    multiple
        If a field can accept multiple same name values. If there are some same
        name fields, and you pass multiple parameter to True, the result will
        be a list but not a single value. 
        
        .. note::
        
            Uliweb Form can't corrently create HTML code for the field with
            multiple values, so you can't simple use ``{{<< form}}`` to render the
            form, but create the form code manually.
            
    idtype
        Indicating how to create an id attribute for html code of a field. If 
        ``None``, it'll not create ``id`` attribute. If it's ``name``, it'll use 
        ``field_<name>`` format to create ``id`` attribute. Others will use
        ``field_<no>``, and ``no`` is a unique number of a field.
