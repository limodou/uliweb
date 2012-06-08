from uliweb.core.template import BaseBlockNode
from uliweb import functions

class PermissionNode(BaseBlockNode):
    def __init__(self, name='', content=None):
        super(PermissionNode, self).__init__(name, content)
        self.nodes = ['if functions.has_permission(request.user, "%s"):\n' % self.name]
        
    def end(self):
        self.nodes.append('pass\n')

class RoleNode(PermissionNode):
    def __init__(self, name='', content=None):
        super(RoleNode, self).__init__(name, content)
        self.nodes = ['if functions.has_role(request.user, "%s"):\n' % self.name]
    