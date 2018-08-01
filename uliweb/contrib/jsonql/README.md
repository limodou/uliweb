# JSONAPI

JsonAPI used to provide commonly schema query language interface, it's inspired by
graphapi and apijson. You can defined json format query data to get data from remote.

## Specification Description

### Schema Definition

```
from uliweb.contrib.jsonql import *

class User(schema):
    username = Type('str', 'Username')
    age = Type('int', 'Age')
```

Above definition defines common schema without Model relatived. If you want to use
Model you can:

```
from uliweb.contrib.jsonql import *

class User(schema):
    __model__ = 'user'

    username = Type('str', 'Username')
    age = Type('int', 'Age')
```

So all fields from `user` model will be derived, and you can also overwrite them with
providing same named field definition. So that you want to overwrite label of field or
special process of it.

You can also provied other meta data to defined a Schema, just like:

```
__table__ # not use model but table
__fields__ # model or table fields, if not provided, it'll use all column of model or table
```

## Query Data

### Query One Row

```
{
    User: {
        username: 'guest'
        '@columns': ['username']
    }
}
```

It'll output:

```
{
    User: {
        '$username': 'guest'
    },
    status: 'success',
    message: 'Process success'
}
```

It equals `select username from user where user.username = 'guest'`. If not `@columns`
provided, it'll use all fields of Schema.

If the field starts with '$', it means `condition`, the condition format can be

```
'$fieldname': value
```

It'll be convert to `fieldname = value`

If the field starts with not '$' or '@', it just likes '@columns', and the value of
the field could be treat parameter, if there is a resolve function in backend. If no
resolve function existed, the value is useless. And if the value is dict type, it'll
be treat a nested schema.

For example:

```
{
    User: {
        username: '',
        birth: '',
        'Article[]:articles': {
            '@limit': 10
        }
    }
}

### Query Multiple Rows

```
{
    'User[]': {
        '$age': '> 30',
        '@page': 1, # begin starts with 1
        '@limit': 10,
        '@total': true, # it'll return total result
    }
}
```

It'll output:

```
{
    'User[]': {
        data: [
            { username: 'guest' }
        ],
        total: 1
    },
    status: 'success'
    message: 'success'
}
```

Full formats should be:

```
fieldname: value # = value
fieldname: '= value' # = value
fieldname: '%value%' # like '%value%'
fieldname: '%value' # like '%value'
fieldname: 'value%' # like 'value%'
fieldname: 'like value' # like value
fieldname: '> value'
fieldname: '< value'
fieldname: '>= value'
fieldname: '<= value'
fieldname: '!= value'
fieldname: [value1, value2], #in (value1, value2)
fieldname: 'in [value1, value2]', # in (value1, value2)
fieldname: 'between [value1, value2]' # between (value1, value2)
```

### Meta Field

Field name starts with '@' defined in query json can be called `Meta Field`, the list
is:

|--------------|---------------|
|Name | Description |
|--------------|---------------|
|@columns | Columns will be returned. If not provided, it'll return full field of Schema. |
|@page | Page number (Multiple Rows) |
|@limit | Rows' number per page (Multiple Rows). |
|@total | If return total value of query ((Multiple Rows). |
|@order_by | It could be a list, just like: ['field.desc', 'field'] |
|--------------|---------------|

### Function Support

You can define function in `@columns` field, just like:

```
{
    'User':{
        '@columns': ['count(id):count']
    }
}
```

### Alias of Schema and Column

You can change result name of Schema via:

```
{
    'User:user':{
        '$id': 1
    }
}
```

It'll output like:

```
{
    user: {
        username: 'guest'
    }
}
```

You can also change column label, just like:

```
{
    'User':{
        '@columns': ['count(id):count']
    }
}
```

It'll output like:

```
{
    User: {
        count: 1
    }
}
```