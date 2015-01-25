head_template = """
digraph name {
  fontname = "{{=fontname}}"
  fontsize = 10
  ratio = auto
  rankdir = LR

  node [
    fontname = "{{=fontname}}"
    fontsize = 10
    shape = "plaintext"
  ]
  edge [
    fontname = "{{=fontname}}"
    fontsize = 10
  ]

"""

body_template = """
{{ if use_subgraph: }}
subgraph {{= cluster_app_name }} {
  label=<
        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
         <TR>
          <TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER">
           <FONT FACE="{{=fontname}} Bold" COLOR="Black" POINT-SIZE="12">{{= app_name }}</FONT>
          </TD>
         </TR>
        </TABLE>
        >
  color=olivedrab4
  style="rounded"
{{ pass }}

  {{ for model in models: }}
    {{= model['app_name'] }}_{{= model['name'] }} [label=<
    <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0">
     <TR><TD COLSPAN="3" CELLPADDING="4" ALIGN="CENTER" BGCOLOR="olivedrab4">
      <FONT FACE="{{=fontname}} Bold" COLOR="white">{{= model['label'] }}</FONT>
      </TD></TR>
      {{ for i, field in enumerate(model['fields']): }}
      {{if i%2==1:}}
        {{color=' BGCOLOR="whitesmoke"'}}
      {{else:}}
        {{color=''}}
      {{pass}}
      {{if field['type'] == 'ManyToMany':}}
        {{color=' BGCOLOR="lightskyblue"'}}
      {{elif field['type'] == 'Reference':}}
        {{color=' BGCOLOR="khaki"'}}
      {{elif field['type'] == 'OneToOne':}}
        {{color=' BGCOLOR="thistle"'}}
      {{elif field['primary_key']:}}
        {{color=' BGCOLOR="lightsalmon"'}}
      {{pass}}
      <TR>
       <TD ALIGN="LEFT" BORDER="0"{{=color}}>
        <FONT FACE="{{=fontname}}">{{= field['label']}}</FONT>
       </TD>
       <TD ALIGN="LEFT"{{=color}}>
        <FONT FACE="{{=fontname}}">{{= field['type_name'] }}</FONT>
       </TD>
       <TD ALIGN="LEFT"{{=color}}>
        <FONT FACE="{{=fontname}}">{{= field['relation'] or ' ' }}</FONT>
       </TD>
      </TR>
      {{ pass }}
    
    </TABLE>
    >]
  {{ pass }}

{{ if use_subgraph: }}
}
{{ pass }}

"""

rel_template = """
  {{ for model in models: }}
    {{ for relation in model['relations']: }}
        {{ if relation['needs_node']: }}
            {{= relation['target_app'] }}_{{= relation['target'] }} [label=<
                <TABLE BGCOLOR="palegoldenrod" BORDER="0" CELLBORDER="0" CELLSPACING="0">
                 <TR>
                  <TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER" BGCOLOR="olivedrab4">
                   <FONT FACE="{{=fontname}} Bold" COLOR="white">{{= relation['target'] }}</FONT>
                  </TD>
                 </TR>
                </TABLE>
                >];
        {{ pass }}
        {{= model['app_name'] }}_{{= model['name'] }} -> {{= relation['target_app'] }}_{{= relation['target'] }}
        [label="{{= relation['label'] }}"] {{= relation['arrows'] }};
    {{ pass }}
  {{ pass }}
"""

tail_template = """
}
"""
def get_model_tables(tables, appname):
    t = []
    for tablename, m in tables.iteritems():
        if hasattr(m, '__appname__') and m.__appname__ == appname:
            t.append(tablename)
    return t

def generate_dot(tables, apps, engine_name=None, fontname=None, **kwargs):
    from uliweb.orm import (get_model, OneToOne, ReferenceProperty,
                            ManyToMany, engine_manager, Model)
    from uliweb.core.template import template

    graphs = []
    table_apps = set([t.__appname__ for t in tables.values()])
    apps = list( table_apps | set(list((apps or []))))

    visited_models = set(tables)
    models = {}
    apps_graph = {}
    nodes = []
    fontname = fontname or 'Helvetica'

    def get_graph(name):
        graph = apps_graph.get(name)
        if not graph:
            graph = {
                'name': '"%s"' % app,
                'app_name': app,
                'fontname': fontname,
                'cluster_app_name': "cluster_%s" % app.replace('.', '_'),
                #only name in tables'app will use subgraph
                'use_subgraph': False, #bool(name in table_apps),
                'models': []
            }
            apps_graph[name] = graph
            graphs.append(graph)
        return graph

    def make_model_info(M):
        model = models.get(M.tablename)
        if model: return model
        model = {
            'app_name': M.table.__appname__.replace('.', '_'),
            'name': M.tablename,
            'fields': [],
            'relations': [],

        }
        model['label'] = M.tablename
        if model['name'] not in models:
            models[M.tablename] = model
            get_graph(M.table.__appname__)['models'].append(model)
        return model

    def add_relation(model, field, extras="", rel='', target_app=None):
        label = "%s(%s)" % (field.property_name, rel)
        target_app = (target_app or field.reference_class.table.__appname__).replace('.', '_')
        target = field.reference_class.tablename
        _rel = {
            'target_app': target_app,
            'target': target,
            'type': type(field).__name__,
            'name': field.property_name,
            'label': label,
            'arrows': extras,
            'needs_node': True
        }
        name = target_app+'_'+target
        if name in nodes:
            _rel['needs_node'] = False
        else:
            _model = {
                'app_name': target_app.replace('.', '_'),
                'name': target,
                'label': target,
                'fields': [],
                'relations': []
            }
            if target not in models:
                models[target] = _model
                graph = apps_graph.get(target_app)
                if not graph:
                    graph = {
                        'name': '"%s"' % target_app,
                        'app_name': target_app,
                        'fontname': fontname,
                        'cluster_app_name': "cluster_%s" % target_app.replace('.', '_'),
                        'use_subgraph': False,
                        'models': []
                    }
                    graphs.append(graph)
                    apps_graph[target_app] = graph
                graph['models'].append(_model)
            else:
                _rel['needs_node'] = False
            nodes.append(name)

        if _rel not in model['relations']:
            model['relations'].append(_rel)


    for app in apps:
        graph = get_graph(app)

        t = get_model_tables(tables, app)
        if not t: continue
        for tablename in t:
            try:
                M = get_model(tablename)
            except:
                continue

            model = make_model_info(M)

            # model attributes
            def add_attributes(field):
                if field.verbose_name:
                    label = "%s(%s)" % (field.property_name, field.verbose_name)
                else:
                    label = "%s" % field.property_name

                d = field.to_column_info()
                # if not isinstance(field, ManyToMany):
                #     d = field.to_column_info()
                # else:
                #     d = {
                #     'name': field.property_name,
                #     'type': ' ',
                #     'relation': 'ManyToMany(%s)' % field.reference_class.__name__,
                #     'primary_key': False
                #     }
                d['label'] = label
                model['fields'].append(d)


            for k, field in M._fields_list:
                add_attributes(field)

            for k, field in M._fields_list:
                if field.__class__ is OneToOne:
                    add_relation(model, field, '[dir=both arrowhead=none arrowtail=none]', rel='1:1')
                elif field.__class__ is ReferenceProperty:
                    add_relation(model, field, rel='n:1')
                elif field.__class__ is ManyToMany:
                    add_relation(model, field, '[dir=both arrowhead=normal arrowtail=normal]', rel='m:n')

    #process the rest models
    engine = engine_manager[engine_name]
    for tablename, m in engine.models.items():
        if tablename not in visited_models:
            M = get_model(tablename)
            appname = M.table.__appname__
            if appname in apps:
                for k, field in M._fields_list:
                    if field.__class__ is OneToOne:
                        name = field.reference_class.tablename
                        target_app = field.reference_class.table.__appname__
                        if name in tables:
                            model = make_model_info(M)
                            add_relation(model, field,
                                         '[dir=both arrowhead=none arrowtail=none color=red]',
                                         rel='1:1',
                                         target_app=target_app)
                    elif field.__class__ is ReferenceProperty:
                        name = field.reference_class.tablename
                        target_app = field.reference_class.table.__appname__
                        if name in tables:
                            model = make_model_info(M)
                            add_relation(model, field, '[color=red]',
                                         rel='n:1',
                                         target_app=target_app)
                    elif field.__class__ is ManyToMany:
                        name = field.reference_class.tablename
                        target_app = field.reference_class.table.__appname__
                        if name in tables:
                            model = make_model_info(M)
                            add_relation(model, field,
                                         '[dir=both arrowhead=normal arrowtail=normal color=red]',
                                         rel='m:n',
                                         target_app=target_app)

    nodes = []
    for graph in graphs:
        nodes.extend([e['name'] for e in graph['models']])

    #create dot file
    dot = template(head_template, graph)

    for graph in graphs:
        # don't draw duplication nodes because of relations
        for model in graph['models']:
            for relation in model['relations']:
                if relation['target'] in nodes:
                    relation['needs_node'] = False
        # render templates
        dot += '\n' + template(body_template, graph)

    for graph in graphs:
        dot += '\n' + template(rel_template, graph)

    dot += '\n' + tail_template
    return dot

def generate_file(tables, apps, outputfile, format='svg', engine_name=None, fontname=None,
                  **kwargs):
    import os
    from uliweb.utils.common import get_tempfilename, get_tempfilename2
    import subprocess as sub

    result = generate_dot(tables, apps, engine_name=engine_name, fontname=fontname, **kwargs)
    dot_fd, dot_filename = get_tempfilename2('dot_', dir=None, suffix='.dot')
    try:
        os.write(dot_fd, result)
    finally:
        os.close(dot_fd)
    if outputfile:
        _o = '-o%s ' % outputfile
    else:
        _o = ''
    cmd = 'dot -T%s %s%s' %(format, _o, dot_filename)
    try:
        result = sub.check_output(cmd, shell=True, cwd=os.getcwd())
        return result
    finally:
        os.remove(dot_filename)
