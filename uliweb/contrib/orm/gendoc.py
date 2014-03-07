
def get_model_tables(tables, appname):
    t = []
    for tablename, m in tables.iteritems():
        if hasattr(m, '__appname__') and m.__appname__ == appname:
            t.append(tablename)
    return t

def safe_str(s, encoding='utf-8'):
    if isinstance(s, unicode):
        return s.encode(encoding)
    else:
        return str(s)


def generate_html(tables, apps, **kwargs):
    from uliweb import orm
    from os.path import dirname, join    
    from uliweb.core.template import template_file
    from uliweb.orm import ReferenceProperty
    from uliweb.utils.textconvert import text2html
    from sqlalchemy.schema import CreateIndex
    
    menus = []
    for app in apps:
        section = {
            'name': '%s' % app,
            'items': []
        }

        t = get_model_tables(tables, app)
        if not t: continue
        for tablename in t:       
            item = {
                'app_name': app.replace('.', '_'),
                'name': tablename,
                'caption': tablename,
            }
            try:
                M = orm.get_model(tablename)
            except:
                continue     
            
            item['label'] = getattr(M, '__verbose_name__', tablename)
            if tablename != M.tablename:
                item['caption'] += ' - ' + M.tablename
            
            section['items'].append(item)
        menus.append(section)
    
    
    all_tables = []
    for name, t in sorted(tables.iteritems()):
        model = {
            'name': name,
            'fields': [],
            'relations': [],
            'choices': [],
            'indexes': [],
        }
        if hasattr(t, '__appname__') :
            model['appname'] = text2html(t.__appname__)
        else :
            model['appname'] = None
        
        M = None
        try:
            M = orm.get_model(name)
        except:
            pass
    
        if getattr(M, '__verbose_name__', None):
            model['label'] = "%s(%s)" % (name, getattr(M, '__verbose_name__', None))
        else:
            model['label'] = name
        if name != getattr(M, 'tablename', name):
            model['label'] += ' - ' + M.tablename
            
        #Add docstring for Model
        if M.__doc__:
            model['desc'] = M.__doc__
        else:
            model['desc'] = ''
        
        #process indexes
        for x in t.indexes:
            model['indexes'].append(CreateIndex(x))
        
        star_index = 0
        for tablefield in sorted(t.c, key=lambda x:(x.name)):
            field = {
                'name': tablefield.name,
                'type': tablefield.type,
                'nullable': tablefield.nullable,
                'primary_key': tablefield.primary_key
            }
            field['reftable'] = None
            field['star'] = False
            field['label'] = "%s" % tablefield.name
            
            if M:
                ppp =  M.properties[tablefield.name]
                if getattr(ppp, 'verbose_name', None):
                    field['label'] = "%s" % (getattr(ppp, 'verbose_name', None))
                
                if getattr(ppp, 'choices', None):
                    choices_list = getattr(ppp, 'choices', None)
                    if callable(choices_list) :
                        choices_list = choices_list()
                    if choices_list :
                        star_index = star_index + 1
                        model['choices'].append({
                            'index': star_index , 
                            'fieldlabel':field['label'], 
                            'fieldname':field['name'], 
                            'list':choices_list})
                        field['star'] = star_index
    
                if ppp and ppp.__class__ is ReferenceProperty:
                    field['reftable'] = "%s" % ppp.reference_class.tablename


            model['fields'].append(field)
        all_tables.append(model)
    database = {}
    database["menus"] = menus;
    database["tables"] = all_tables;
    return template_file(join(dirname(__file__), "templates/docindex.html"), database)
    
    
