from uliweb.core.SimpleFrame import url_for

def menu(request, current):
     return [
      [current=='Portal', 'Home', url_for('Portal.views.index')],
      [current=='Documents', 'Documents', url_for('Documents.views.documents')],
#      [current=='Examples', 'Examples', url_for('Examples.views.examples_index')],
      [current=='About', 'About', url_for('Documents.views.show_document', filename='introduction')],
    ]
    