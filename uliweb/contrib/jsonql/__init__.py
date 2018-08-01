#coding=utf8

from uliweb import settings
from uliweb.utils.common import safe_str, import_attr
from uliweb.utils.storage import Storage
from uliweb.orm import do_, get_model
from uliweb.utils.sorteddict import SortedDict
from sqlalchemy import __version__ as sa_version, select, true, text, literal
import logging

DEBUG = False
__schemas__ = {}
__relations__ = None
__default_limit__ = 10

log = logging.getLogger(__name__)


class ModelError(Exception): pass
class SchemaError(Exception): pass
class RelationError(Exception): pass


class Type(object):
    creation_counter = 1

    def __init__(self, type='str', label='', field_name=None, **kwargs):
        self.type = type
        self.label = label
        self.field_name = field_name
        self.name = None
        self.kwargs = kwargs
        self.creation_counter = Type.creation_counter
        Type.creation_counter += 1

class SchemaMetaClass(type):
    def __init__(cls, name, bases, dct):
        super(SchemaMetaClass, cls).__init__(name, bases, dct)
        if name == 'Schema':
            return

        cls.properties = {}
        cls._fields_list = []
        cls._collection_names = {}
        cls._bind()

        for attr_name in dct.keys():
            attr = dct[attr_name]
            if isinstance(attr, Type):
                attr.name = attr_name
                cls.properties[attr_name] = attr

        fields_list = [(k, v) for k, v in cls.properties.items()]
        fields_list.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))
        cls._fields_list = [k for k,v in fields_list]

        cls._bind_query()


def reflect_column(column):
    type_name = column.type.__class__.__name__.lower()
    kwargs = SortedDict()
    field_type = type_name

    if type_name in ('char', 'varchar'):
        kwargs['max_length'] = column.type.length
    elif type_name in ('text', 'blob', 'integer', 'float', 'bigint'):
        pass
    elif type_name == 'long':
        field_type = 'bigint'
    elif type_name in ('clob',):
        field_type = 'text'
    elif type_name in ('decimal', 'float'):
        kwargs['precision'] = column.type.precision
        kwargs['scale'] = column.type.scale
    elif type_name == 'raw':  # oracle
        field_type = 'binary'
        kwargs['max_length'] = column_type.length
    elif type_name == 'number':
        if column.type.scale:
            kwargs['precision'] = column.type.precision
            kwargs['scale'] = column.type.scale
            field_type = 'decimal'
        else:
            field_type = 'int'
    elif type_name == 'numeric':
        field_type = 'decimal'
        kwargs['precision'] = column.type.precision
        kwargs['scale'] = column.type.scale
    elif type_name in ('timestamp',):
        field_type = 'timestamp'
    elif type_name in ('datetime', 'date', 'time'):
        pass
    # for tinyint will be treated as bool
    elif type_name in ('tinyint', 'boolean'):
        field_type = 'bool'
    else:
        raise ValueError("Don't support column [{0}] for type [{1}] when parsing {2}".format(column.name, type_name, column.table.name))

    if sa_version >= '1.2' and column.comment:
        kwargs['label'] = column.comment

    if not kwargs.get('label'):
        kwargs['label'] = column.name

    return field_type, kwargs

class Schema(object):
    __metaclass__ = SchemaMetaClass
    __model__ = None #Model name
    __table__ = None #table name
    __fields__ = []
    __query__ = None

    @classmethod
    def __repr__(cls):
        d = []
        d.append('{}{{'.format(cls.__name__))
        for name in cls._fields_list:
            f = cls.properties[name]
            field_name = ''
            if f.field_name:
                field_name = ' ,field_name={}'.format(f.field_name)
            d.append('    {}(type=\'{}\', label=\'{}\'{})'.format(f.name, f.type, safe_str(f.label), field_name))
        d.append('}')
        return '\n'.join(d)

    @classmethod
    def _bind(cls):
        from uliweb.orm import reflect_table

        if not cls.__table__ is not None and cls.__model__:
            model = get_model(cls.__model__)
            if not model:
                raise ModelError('Model {} can not be found'.format(cls.__model__))
            cls.__table__ = model.table
        if cls.__table__ is not None:
            cls.__table__ = reflect_table(cls.__table__)
            for f in (cls.__fields__ or cls.__table__.columns.keys()):
                col = cls.__table__.columns.get(f)
                if col is not None:
                    field_type, kwargs = reflect_column(col)
                    field = Type(field_type, **kwargs)
                    field.name = f
                    cls.properties[f] = field
                else:
                    raise FieldError('Field {} can not be found in table {}'.format(f, cls.table.name))

    @classmethod
    def _bind_query(cls):
        if cls.__table__ is not None and not cls.__query__:
            fields = []
            for f in cls.properties.values():
                name = f.field_name or f.name
                col = cls.__table__.columns.get(name)
                if col is not None:
                    fields.append(col)
            cls.__query__ = select(fields, from_obj=[cls.__table__])

    @classmethod
    def get_column(cls, name):
        alias = ''
        if ':' in name:
            name, alias = [x.strip() for x in name.split(':')]
        col = cls.__table__.columns.get(name)
        if col is None:
            if alias:
                col = text(name + ' as ' + alias)
            else:
                col = text(name)
        else:
            if alias:
                col = col.label(alias)
        return col

class Relation(object):
    def __init__(self, relation):
        self._schema_a = None  # schema class
        self._schema_b = None
        self._schema_a_name = None
        self._schema_b_name = None
        self._fields_a = set()
        self._fields_b = set()
        self.relation_key = None  # saving [(schema_a, schema_b), (schema_b, schema_a)]
        self.cached = {}

        if not isinstance(relation, (tuple, list)):
            relation = [relation]
        for v in relation:
            t1, t2 = [x.strip() for x in v.split('=')]
            schema_a_name, field_a_name = t1.split('.')
            schema_b_name, field_b_name = t2.split('.')
            key = (schema_a_name, schema_b_name)
            if self.relation_key and key not in self.relation_key:
                raise RelationError('Relation {!r} is not matched with before value {!r}'.format(
                    key, self.relation_key))
            self._schema_a_name = schema_a_name
            self._schema_b_name = schema_b_name
            self.relation_key = [key, (schema_b_name, schema_a_name)]
            self._fields_a.add((field_a_name, field_b_name))
            self._fields_b.add((field_b_name, field_a_name))

    @property
    def schema_a(self):
        if not self._schema_a:
            self._schema_a = get_schema(self._schema_a_name)
        return self._schema_a

    @property
    def schema_b(self):
        if not self._schema_b:
            self._schema_b = get_schema(self._schema_b_name)
        return self._schema_b

    def __eq__(self, key):
        """

        :param key: (schema_a, schema_b)
        :return:
        """
        return key in self.relation_key

    def get_condition(self, key):
        condition = None
        a, b = key
        if not self == key:
            return condition

        condition = self.cached.get(key)
        if not condition:
            condition = true()
            if a == self._schema_a_name:
                for fa, fb in self._fields_a:
                    condition = (self.schema_a.get_column(fa) == self.schema_b.get_column(fb)) & condition
            else:
                for fb, fa in self._fields_b:
                    condition = (self.schema_b.get_column(fb) == self.schema_a.get_column(fa)) & condition
            self.cached[key] = condition

        return condition


class Relations(object):
    def __init__(self):
        self.relations = {}

    def add(self, relation):
        """
        relation is a string list, just like:
        ['User.id = Group.user', 'User.username = Group.username']
        :param relation:
        :return:
        """
        r = Relation(relation)
        key = r.relation_key[0]
        if key not in self.relations:
            self.relations[key] = r
            self.relations[r.relation_key[1]]= r

    def get_condition(self, relation):
        """

        :param relation: (schema_a, schema_b)
        :return:
        """
        condition = None
        r = self.relations.get(relation)
        if r:
            condition = r.get_condition(relation)
        return condition


__relations__ = Relations()


def add_relation(relation):
    global __relations__

    __relations__.add(relation)


def get_relation_condition(key):
    """
    Get relation condition
    :param key: should be (schema_a, schema_b)
    :return:
    """
    global __relations__

    return __relations__.get_condition(key)


def get_schema(name, exception=True):
    global __schemas__

    s = __schemas__.get(name)
    if not s and exception:
        raise SchemaError('Schema {} can not be found in settings.'.format(name))
    return s


class Query(object):
    def __init__(self, data):
        self.data = data

    def run(self):
        data = {}
        for name, param in self.data.items():
            k, result = self.query_schema(name, param)
            data[k] = result
        return data

    def parse_entry(self, name):
        """
        Parse query entry name, just like:
        {
            'User[]:user'
        }

        'User[]:user' is an entry name.

        :param name:
        :return:
        """

        # calculate schema mode
        # if ':name' or '' or '[]:name' or '[]' found, it'll be treat as multiple Schema query
        alias = name
        if ':' in name:
            name, alias = name.split(':')
        if name.endswith('[]'):
            need_list = True
            name = name[:-2]
        else:
            need_list = False
        return alias, name, need_list

    def query_schema(self, name, param):
        """
        If name includes '[]', then it'll return a list
        :param name: schema name
        :param param: json parameters
        :return:
        """

        alias, name, need_list = self.parse_entry(name)

        if not name:
            result = self.process_multiple_query(need_list, param)
        else:
            result = self.process_single_query(name, need_list, param)
        return alias, result

    def parse_condition(self, schema, name, v):
        """
        Parse name = 'value' to condition
        :param name: column name
        :param schema: schema name
        :param v: column value
        :return:
        """

        S = schema
        col = S.get_column(name)
        condition = None

        if col is not None:  # can create condition
            if isinstance(v, (str, unicode)):
                if v.startswith('>='):
                    condition = (col >= eval(v[2:].strip()))
                elif v.startswith('>'):
                    condition = (col > eval(v[1:].strip()))
                elif v.startswith('<='):
                    condition = (col <= eval(v[2:].strip()))
                elif v.startswith('<'):
                    condition = (col < eval(v[1:].strip()))
                elif v.startswith('='):
                    condition = (col == eval(v[1:].strip()))
                elif v.startswith('!='):
                    condition = (col != eval(v[2:].strip()))
                elif v.startswith('like'):
                    condition = col.like(v[4:].strip())
                elif v.startswith('between'):
                    _v = eval(v[7:].strip())
                    if not isinstance(_v, (tuple, list)):
                        raise ValueError("Between operation should be a list, but {!r} found".format(v))
                    condition = (col.between(*_v))
                elif v.startswith('in'):
                    condition = (col.in_(eval(v[2:].strip())))
                else:
                    if '%' in v:  # like
                        condition = col.like(v)
                    else:
                        condition = (col == v)
            elif isinstance(v, (tuple, list)):
                condition = (col.in_(v))
            else:
                condition = (col == v)
        return condition

    def parse_param(self, name, param):
        """
        Parse schema parameter, it'll return
        {
            condition
            columns
            limit
            order_by
            group_by
            total
            page
            table
            name #schema name
        }
        :param name: schema name
        :param param: schema query parameter
        :return: dict
        """
        S = get_schema(name)

        # prepare condition
        condition = true()
        fields = []
        columns = []
        columns_param = {}
        limit = __default_limit__
        order_by = []
        group_by = []
        total = None
        page = 0
        table = S.__table__
        relation = None

        for k, v in param.items():
            if k.startswith('@'):
                if k == '@columns':
                    fields = v[:]
                elif k == '@limit':
                    limit = v
                elif k == '@page':
                    page = v
                elif k == '@order_by':
                    if isinstance(v, (str, unicode)):
                        orders = v.split(',')
                    else:
                        orders = v
                    for c in orders:
                        if '.' in c:
                            col_name, dir = c.split('.')
                        else:
                            col_name = c
                            dir = 'asc'
                        col = S.get_column(col_name)
                        if dir == 'desc':
                            order_by.append(col.desc())
                        else:
                            order_by.append(col)
                elif k == '@group_by':
                    if isinstance(v, (str, unicode)):
                        groups = v.split(',')
                    else:
                        groups = v
                    for c in groups:
                        col = S.get_column(c)
                        group_by.append(col)
                elif k == '@total':
                    total = v
                elif k == '@relation':
                    relation_key = name, v
                    relation = get_relation_condition(relation_key)
            elif k.startswith('$'):  # condition
                c = self.parse_condition(S, k[1:], v)
                if c is not None:
                    condition = c & condition
            elif isinstance(v, dict):  # guest schema
                # todo nested schema
                # if there is not one row, it'll using left join otherwise using standalone
                # query
                nested_alias, nested_name, nested_need_list = self.parse_entry(k)
                nested_config = self.parse_param(nested_name, value)
                if nested_need_list:
                    # insert resolve function
                    pass
                else:
                    relation = name, nested_config.name
                    outerjoin_condition = get_relation_condition(relation)
                    if outerjoin_condition is None:
                        raise RelationError("Relation between {!r} can not be found".format(relation))
                    table.outerjoin(nested_config.table, outerjoin_condition)
                    condition = nested_config.condition & condition
                    columns.extend(nested_config.columns)

            else:
                # columns
                if k not in fields:
                    fields.append(k)

        columns.extend([S.get_column(x) for x in fields or S._fields_list])  # used for select

        config = Storage({})
        config.table = table
        config.condition = condition
        config.columns = columns
        config.columns_param = columns_param
        config.total = total
        config.limit = limit
        config.page = page
        config.order_by = order_by
        config.group_by = group_by
        config.name = name
        config.schema = S
        config.relation = relation

        return config

    def parse_multiple_query(self, param):
        tables = []
        condition = true()
        order_by = []
        group_by = []
        limit = __default_limit__
        total = None
        page = 0
        columns = []

        for k, v in param.items():
            if isinstance(v, dict):  # Schema
                c = self.parse_param(k, v)
                tables.append(c.table)
                columns.extend(c.columns)
                condition = c.condition & condition
                if c.relation is not None:
                    condition = c.relation & condition
            else:
                if k.startswith('@'):
                    if k == '@limit':
                        limit = v
                    elif k == '@page':
                        page = v
                    elif k == '@order_by':
                        if isinstance(v, (str, unicode)):
                            orders = v.split(',')
                        else:
                            orders = v
                        for c in orders:
                            if '.' in c:
                                v = c.split('.')
                                if len(v) == 3:
                                    schema_name, col_name, dir = v
                                else:
                                    schema_name, col_name = v
                                    dir = 'asc'
                            else:
                                col_name = c
                                dir = 'asc'
                            S = get_schema(schema_name)
                            col = S.get_column(col_name)
                            if dir == 'desc':
                                order_by.append(col.desc())
                            else:
                                order_by.append(col)
                    elif k == '@group_by':
                        if isinstance(v, (str, unicode)):
                            groups = v.split(',')
                        else:
                            groups = v
                        for c in groups:
                            if '.' in c:
                                schema_name, col_name = c.split('.')
                            S = get_schema(schema_name)
                            col = S.get_column(col_name)
                            group_by.append(col)
                    elif k == '@total':
                        total = v

        config = Storage({})
        config.tables = tables
        config.condition = condition
        config.columns = columns
        config.order_by = order_by
        config.group_by = group_by
        config.page = page
        config.limit = limit
        config.total = total

        return config

    def process_multiple_query(self, need_list, param):
        config = self.parse_multiple_query(param)
        count = 0

        query = select(config.columns, config.condition, from_obj=config.tables)
        if need_list:
            if config.order_by:
                query = query.order_by(*config.order_by)
            if config.group_by:
                query = query.group_by(*config.group_by)
            if config.total:
                if DEBUG:
                    log.debug('Query Schema {} Count:'.format(config.name))
                    log.debug(query.count())
                count = do_(query.count()).scalar()
            if config.page > 0:
                query = query.limit(config.limit).offset((config.page-1)*config.limit)
            if DEBUG:
                log.debug('Query Schema {}:'.format(config.name))
                log.debug(query)
            result = {'data': [dict(row) for row in do_(query)]}
            if config.total:
                result['total'] = count
        else:
            query = query.limit(1)
            if DEBUG:
                log.debug('Query Schema {}:'.format(config.name))
            result = list(do_(query))
            if result:
                result = dict(result[0])
            else:
                result = {}
        return result

    def process_single_query(self, name, need_list, param):
        config = self.parse_param(name, param)
        count = 0

        query = select(config.columns, config.condition, from_obj=[config.table])
        if need_list:
            if config.order_by:
                query = query.order_by(*config.order_by)
            if config.group_by:
                query = query.group_by(*config.group_by)
            if config.total:
                if DEBUG:
                    log.debug('Query Schema {} Count:'.format(config.name))
                    log.debug(query.count())
                count = do_(query.count()).scalar()
            if config.page > 0:
                query = query.limit(config.limit).offset((config.page-1)*config.limit)
            if DEBUG:
                log.debug('Query Schema {}:'.format(config.name))
                log.debug(query)
            result = {'data': [dict(row) for row in do_(query)]}
            if config.total:
                result['total'] = count
        else:
            query = query.limit(1)
            if DEBUG:
                log.debug('Query Schema {}:'.format(config.name))
            result = list(do_(query))
            if result:
                result = dict(result[0])
            else:
                result = {}
        return result


def query(d):
    """
    Query schema
    :param d: dict options
    :return:
    """
    q = Query(d)
    return q.run()


def after_init_apps(sender):
    global __schemas__, __default_limit__

    if 'JSONQL_SCHEMA' in settings:
        for name, model_path in settings.JSONQL_SCHEMA.items():
            if not model_path: continue
            if isinstance(model_path, (str, unicode)):
                path = model_path
            else:
                raise Exception("Schema path should be a string but %r found" % model_path)

            __schemas__[name] = import_attr(model_path)
    __default_limit__ = settings.JSONQL.get('limit', 10)