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
            print '==============='
        __mc__ = MC
    return __mc__

def find_model(sender, model_name):
    """
    Register new model to ORM
    """
    MC = get_mc()
    model = MC.get(MC.c.name==model_name)
    if model:
        model_inst = model.get_instance()
        orm.set_model(model_name, model_inst.table_name, appname=__name__, model_path='')
        return orm.__models__.get(model_name)

def load_models(sender):
    MC = get_mc()
    if MC:
        for row in MC.all():
            functions.get_model(str(row.name))

def get_model(sender, model_name, model_inst, model_info, model_config):
    """
    #todo Add objcache support
    """
    MC = get_mc()
    if MC:
        model = MC.get(MC.c.name==model_name)
        if model:
            cached_inst = __cache__.get(model_name)
            if not cached_inst or (cached_inst and cached_inst[1]!=model.cur_uuid):
                model_inst = model.get_instance()
                M = orm.create_model(model_name, fields=eval(model_inst.fields) or [],
                                     indexes=eval(model_inst.indexes) or [],
                                     basemodel=model_inst.basemodel,
                                     __replace__=True)
                __cache__[model_name] = (M, model.cur_uuid)

                #process extension model
                if model_inst.has_extension:
                    ext_model_name = model_name + '_extension'
                    fields = eval(model_inst.extension_fields) or []
                    fields.insert(0, ('_parent', 'OneToOne', {'reference_class':model_name, 'collection_name':'ext'}))
                    ME = orm.create_model(ext_model_name, fields=fields,
                                          indexes=eval(model_inst.extension_indexes) or [],
                                          basemodel=model_inst.extension_model,
                                          __replace__=True)

            else:
                M = cached_inst[0]

            return M
