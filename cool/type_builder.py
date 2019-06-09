from .cmp import visitor, ErrorType, SelfType, SemanticError
from .parser import ProgramNode, ClassDeclarationNode, AttrDeclarationNode, FuncDeclarationNode

class TypeBuilder:
    def __init__(self, context, errors=[]):
        self.context = context
        self.current_type = None
        self.errors = errors

        # Building built-in types
        self.object_type = self.context.get_type('Object')
        
        self.io_type = self.context.get_type('IO')
        self.io_type.set_parent(self.object_type)

        self.int_type = self.context.get_type('Int')
        self.int_type.set_parent(self.object_type)
        self.int_type.sealed = True

        self.string_type = self.context.get_type('String')
        self.string_type.set_parent(self.object_type)
        self.string_type.sealed = True

        self.bool_type = self.context.get_type('Bool')
        self.bool_type.set_parent(self.object_type)
        self.bool_type.sealed = True

        self.object_type.define_method('abort', [], [], self.object_type)
        self.object_type.define_method('type_name', [], [], self.string_type)
        self.object_type.define_method('copy', [], [], SelfType())
        
        self.io_type.define_method('out_string', ['x'], [self.string_type], SelfType())
        self.io_type.define_method('out_int', ['x'], [self.int_type], SelfType())
        self.io_type.define_method('in_string', [], [], self.string_type)
        self.io_type.define_method('in_int', [], [], self.int_type)

        self.string_type.define_method('length', [], [], self.int_type)
        self.string_type.define_method('concat', ['s'], [self.string_type], self.string_type)
        self.string_type.define_method('substr', ['i', 'l'], [self.int_type, self.int_type], self.string_type)
    
    @visitor.on('node')
    def visit(self, node):
        pass
    
    @visitor.when(ProgramNode)
    def visit(self, node):
        for def_class in node.declarations:
            self.visit(def_class)
            
        try:
            self.context.get_type('Main').get_method('main')
        except SemanticError:
            self.errors.append('The class "Main" and its method "main" are needed.')
            
    
    @visitor.when(ClassDeclarationNode)
    def visit(self, node):
        self.current_type = self.context.get_type(node.id)
        
        if node.parent:
            try:
                parent_type = self.context.get_type(node.parent)
                self.current_type.set_parent(parent_type)
            except SemanticError as ex:
                self.errors.append(ex.text)
                self.current_type.set_parent(self.object_type)
        else:
            self.current_type.set_parent(self.object_type)
        
        for feature in node.features:
            self.visit(feature)
            
    @visitor.when(AttrDeclarationNode)
    def visit(self, node):
        try:
            attr_type = self.context.get_type(node.type)
        except SemanticError as ex:
            self.errors.append(ex.text)
            attr_type = ErrorType()
            
        try:
            self.current_type.define_attribute(node.id, attr_type)
        except SemanticError as ex:
            self.errors.append(ex.text)
        
    @visitor.when(FuncDeclarationNode)
    def visit(self, node):
        arg_names, arg_types = [], []
        for idx, typex in node.params:
            try:
                arg_type = self.context.get_type(typex)
            except SemanticError as ex:
                self.errors.append(ex.text)
                arg_type = ErrorType()
            else:
                if isinstance(arg_type, SelfType):
                    self.errors.append(f'Type "{arg_type.name}" canot be used as parameter type')
                    arg_type = ErrorType()
                
            arg_names.append(idx)
            arg_types.append(arg_type)
        
        try:
            ret_type = self.context.get_type(node.type)
        except SemanticError as ex:
            self.errors.append(ex.text)
            ret_type = ErrorType()
        
        try:
            self.current_type.define_method(node.id, arg_names, arg_types, ret_type)
        except SemanticError as ex:
            self.errors.append(ex.text)