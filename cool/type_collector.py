from .cmp import visitor, Context, SelfType, AutoType, SemanticError
from .parser import ProgramNode, ClassDeclarationNode

ERROR_ON = 'Ln %d, Col %d: '

class TypeCollector(object):
    def __init__(self, errors=[]):
        self.context = Context()
        self.errors = errors

        # Creating special types
        self.context.add_type(SelfType())
        self.context.add_type(AutoType())

        # Creating built-in types
        self.context.create_type('Object')
        self.context.create_type('IO')
        self.context.create_type('Int')
        self.context.create_type('String')
        self.context.create_type('Bool')
    
    @visitor.on('node')
    def visit(self, node):
        pass
    
    @visitor.when(ProgramNode)
    def visit(self, node):       
        for def_class in node.declarations:
            self.visit(def_class)
    
    @visitor.when(ClassDeclarationNode)
    def visit(self, node):
        try:
            self.context.create_type(node.id.lex)
        except SemanticError as ex:
            self.errors.append(ERROR_ON % (node.line, node.column) + ex.text)
