head_template = """
digraph name {
  fontname = "Helvetica"
  fontsize = 10

  node [
    fontname = "Helvetica"
    fontsize = 10
    shape = "plaintext"
  ]
  edge [
    fontname = "Helvetica"
    fontsize = 10
  ]

"""

body_template = """
{{ if use_subgraph: }}
subgraph {{= cluster_app_name }} {
  label=<
        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
        <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER"
        ><FONT FACE="Helvetica Bold" COLOR="Black" POINT-SIZE="12"
        >{{= app_name }}</FONT></TD></TR>
        </TABLE>
        >
  color=olivedrab4
  style="rounded"
{{ pass }}

  {{ for model in models: }}
    {{= model['app_name'] }}_{{= model['name'] }} [label=<
    <TABLE BGCOLOR="palegoldenrod" BORDER="0" CELLBORDER="0" CELLSPACING="0">
     <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER" BGCOLOR="olivedrab4"
     ><FONT FACE="Helvetica Bold" COLOR="white"
     >{{= model['label'] }}</FONT></TD></TR>
      {{ for field in model['fields']: }}
      <TR><TD ALIGN="LEFT" BORDER="0"
      ><FONT {{ if not field['required']: }}COLOR="#7B7B7B" {{ pass }}FACE="Helvetica {{ if not field['required']: }}Italic{{ else: }}Bold{{ pass }}">{{= field['label'] }}</FONT
      ></TD>
      <TD ALIGN="LEFT"
      ><FONT {{ if not field['required']: }}COLOR="#7B7B7B" {{ pass }}FACE="Helvetica {{ if not field['required']: }}Italic{{ else: }}Bold{{ pass }}">{{= field['type'] }}</FONT
      ></TD></TR>
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
                <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER" BGCOLOR="olivedrab4"
                ><FONT FACE="Helvetica Bold" COLOR="white"
                >{{= relation['target'] }}</FONT></TD></TR>
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
    
def generate_dot(tables, apps, **kwargs):
    from uliweb.orm import get_model, OneToOne, ReferenceProperty, ManyToMany
    from uliweb.core.template import template
    
    dot = head_template

    graphs = []
    for app in apps:
        graph = {
            'name': '"%s"' % app,
            'app_name': "%s" % app,
            'cluster_app_name': "cluster_%s" % app.replace('.', '_'),
#            'disable_fields': disable_fields,
            'use_subgraph': True,
            'models': []
        }

        t = get_model_tables(tables, app)
        if not t: continue
        for tablename in t:
            model = {
                'app_name': app.replace('.', '_'),
                'name': tablename,
#                'abstracts': abstracts,
                'fields': [],
                'relations': []
            }
            
            try:
                M = get_model(tablename)
            except:
                continue

            # consider given model name ?
#            def consider(model_name):
#                return not include_models or model_name in include_models
#
#            if not consider(appmodel._meta.object_name):
#                continue

#            if verbose_names and appmodel._meta.verbose_name:
#                model['label'] = appmodel._meta.verbose_name
#            else:
#                model['label'] = model['name']
            if getattr(M, '__verbose_name__', None):
                model['label'] = "%s(%s)" % (tablename, getattr(M, '__verbose_name__', None))
            else:
                model['label'] = tablename
            
            # model attributes
            def add_attributes(field):
                if field.verbose_name:
                    label = "%s(%s)" % (field.property_name, field.verbose_name)
                else:
                    label = "%s" % field.property_name
                    
                model['fields'].append({
                    'name': field.property_name,
                    'label': label,
                    'type': type(field).__name__,
                    'required': field.required,
#                    'abstract': field in abstract_fields,
                })
                    

            for k, field in M._fields_list:
                add_attributes(field)

            if M._manytomany:
                for k, field in M._manytomany.iteritems():
                    add_attributes(field)

            # relations
            def add_relation(field, extras="", rel=''):
                label = "%s(%s)" % (field.property_name, rel)
                    
                _rel = {
                    'target_app': field.reference_class.table.__appname__.replace('.', '_'),
                    'target': field.reference_class.tablename,
                    'type': type(field).__name__,
                    'name': field.property_name,
                    'label': label,
                    'arrows': extras,
                    'needs_node': True
                }
                if _rel not in model['relations']:
                    model['relations'].append(_rel)

            for k, field in M._fields_list:
                if field.__class__ is OneToOne:
                    add_relation(field, '[dir=both arrowhead=none arrowtail=none]', rel='1:1')
                elif field.__class__ is ReferenceProperty:
                    add_relation(field, rel='n:1')

            if M._manytomany:
                for k, field in M._manytomany.iteritems():
                    if field.__class__ is ManyToMany:
                        add_relation(field, '[dir=both arrowhead=normal arrowtail=normal]', rel='m:n')
            graph['models'].append(model)
        graphs.append(graph)

    nodes = []
    for graph in graphs:
        nodes.extend([e['name'] for e in graph['models']])

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
