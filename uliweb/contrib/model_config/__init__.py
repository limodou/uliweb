from uliweb import functions
import uliweb.orm as orm


#key:model_name, value:(Class, uuid)
__cache__ = {}
__mc__ = None

def get_mc():
    global __mc__

    if not __mc__:
        MC = functions.get_model('model_config', signal=False)
        engine = MC.get_engine().engine
        if not MC.table.exists(engine):
            MC.table.create(engine)
        __mc__ = MC
    return __mc__

def find_model(sender, model_name):
    """
    Register new model to ORM
    """
    MC = get_mc()
    model = MC.get((MC.c.model_name==model_name) & (MC.c.uuid!=''))
    if model:
        model_inst = model.get_instance()
        orm.set_model(model_name, model_inst.table_name, appname=__name__, model_path='')
        return orm.__models__.get(model_name)

def load_models(sender):
    MC = get_mc()
    if MC:
        for row in MC.filter(MC.c.uuid!='').fields(MC.c.model_name):
            functions.get_model(str(row.model_name))

def get_model(sender, model_name, model_inst, model_info, model_config):
    """
    #todo Add objcache support
    """
    MC = get_mc()
    if MC:
        model = MC.get((MC.c.model_name==model_name) & (MC.c.uuid!=''))
        if model:
            cached_inst = __cache__.get(model_name)
            if not cached_inst or (cached_inst and cached_inst[1]!=model.uuid):
                model_inst = model.get_instance()
                M = orm.create_model(model_name, fields=eval(model_inst.fields or '[]'),
                                     indexes=eval(model_inst.indexes or '[]'),
                                     basemodel=model_inst.basemodel,
                                     __replace__=True)
                __cache__[model_name] = (M, model.uuid)

                #process extension model
                if model_inst.has_extension:
                    ext_model_name = model_name + '_extension'
                    fields = eval(model_inst.extension_fields or '[]')
                    fields.insert(0, {'name':'_parent', 'type':'OneToOne', 'reference_class':model_name, 'collection_name':'ext'})
                    ME = orm.create_model(ext_model_name, fields=fields,
                                          indexes=eval(model_inst.extension_indexes or '[]'),
                                          basemodel=model_inst.extension_model,
                                          __replace__=True)

            else:
                M = cached_inst[0]

            return M

def get_model_fields(model, add_reserver_flag=True):
    """
    Creating fields suit for model_config , id will be skipped.
    """
    import uliweb.orm as orm

    fields = []
    m = {'type':'type_name', 'hint':'hint',
         'default':'default', 'required':'required'}
    m1 = {'index':'index', 'unique':'unique'}
    for name, prop in model.properties.items():
        if name == 'id':
            continue
        d = {}
        for k, v in m.items():
            d[k] = getattr(prop, v)
        for k, v in m1.items():
            d[k] = bool(prop.kwargs.get(v))
        d['name'] = prop.fieldname or name
        d['verbose_name'] = unicode(prop.verbose_name)
        d['nullable'] = bool(prop.kwargs.get('nullable', orm.__nullable__))
        if d['type'] in ('VARCHAR', 'CHAR', 'BINARY', 'VARBINARY'):
            d['max_length'] = prop.max_length
        if d['type'] in ('Reference', 'OneToOne', 'ManyToMany'):
            d['reference_class'] = prop.reference_class
            #collection_name will be _collection_name, it the original value
            d['collection_name'] = prop._collection_name
        d['server_default'] = prop.kwargs.get('server_default')
        d['_reserved'] = True
        fields.append(d)

    return fields

def get_model_indexes(model, add_reserver_flag=True):
    """
    Creating indexes suit for model_config.
    """
    import uliweb.orm as orm
    from sqlalchemy.engine.reflection import Inspector

    indexes = []
    engine = model.get_engine().engine
    insp = Inspector.from_engine(engine)
    for index in insp.get_indexes(model.tablename):
        d = {}
        d['name'] = index['name']
        d['unique'] = index['unique']
        d['fields'] = index['column_names']
        if add_reserver_flag:
            d['_reserved'] = True
        indexes.append(d)

    return indexes
