from uliweb.core.template import BaseBlockNode

class PermissionNode(BaseBlockNode):
    def generate(self, writer):
        writer.write_line('if functions.has_permission(request.user, %s):' %
                          self.statement, self.line)
        with writer.indent():
            self.body.generate(writer)
            writer.write_line("pass", self.line)

class RoleNode(BaseBlockNode):
    def generate(self, writer):
        writer.write_line('if functions.has_role(request.user, %s):' %
                          self.statement, self.line)
        with writer.indent():
            self.body.generate(writer)
            writer.write_line("pass", self.line)
