import cmp.visitor as visitor
from cmp.semantic import SemanticError
from cmp.semantic import Attribute, Method, Type
from cmp.semantic import SelfType, AutoType, ErrorType
from cmp.semantic import Context, Scope
from cool_parser import ProgramNode, ClassDeclarationNode, AttrDeclarationNode, FuncDeclarationNode
from cool_parser import IfThenElseNode, WhileLoopNode, BlockNode, LetInNode, CaseOfNode
from cool_parser import AssignNode, UnaryNode, BinaryNode, LessEqualNode, LessNode, EqualNode, ArithmeticNode
from cool_parser import NotNode, IsVoidNode, ComplementNode, FunctionCallNode, MemberCallNode, NewNode, AtomicNode
from cool_parser import IntegerNode, IdNode, StringNode, BoolNode
from cool_parser import CoolGrammar, CoolParser
from cool_lexer import tokenizer
from cmp.utils import Token
from cmp.evaluation import evaluate_reverse_parse

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
            self.context.create_type(node.id)
        except SemanticError as ex:
            self.errors.append(ex.text)

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



WRONG_SIGNATURE = 'Method "%s" already defined in "%s" with a different signature.'
SELF_IS_READONLY = 'Variable "self" is read-only.'
LOCAL_ALREADY_DEFINED = 'Variable "%s" is already defined in method "%s".'
INCOMPATIBLE_TYPES = 'Cannot convert "%s" into "%s".'
VARIABLE_NOT_DEFINED = 'Variable "%s" is not defined in "%s".'
INVALID_OPERATION = 'Operation is not defined between "%s" and "%s".'

class TypeChecker:
    def __init__(self, context, errors=[]):
        self.context = context
        self.current_type = None
        self.current_method = None
        self.errors = errors

        # search built-in types
        self.object_type = self.context.get_type('Object')
        self.io_type = self.context.get_type('IO')
        self.int_type = self.context.get_type('Int')
        self.string_type = self.context.get_type('String')
        self.bool_type = self.context.get_type('Bool')
        
    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node, scope=None):
        scope = Scope()
        for declaration in node.declarations:
            self.visit(declaration, scope.create_child())
        return scope

    @visitor.when(ClassDeclarationNode)
    def visit(self, node, scope):
        # check ciclic heritage
        self.current_type = self.context.get_type(node.id)
        
        for feature in node.features:
            if isinstance(feature, AttrDeclarationNode):
                self.visit(feature, scope.create_child())

        for attr in self.current_type.attributes:
            scope.define_variable(attr.name, attr.type)
            
        for feature in node.features:
            if isinstance(feature, FuncDeclarationNode):
                self.visit(feature, scope.create_child())
        
    @visitor.when(AttrDeclarationNode)
    def visit(self, node, scope):
        # check redefined attr

        if node.expression:
            self.visit(node.expression, scope.create_cild())
            expr_type = node.expression.static_type

            node_type = self.current_type.get_attribute(node.id).type
            node_type = self.current_type if isinstance(node_type, SelfType) else node_type
            if not expr_type.conforms_to(node_type):
                self.errors.append(INCOMPATIBLE_TYPES % (expr_type.name, node_type.name))
        

    @visitor.when(FuncDeclarationNode)
    def visit(self, node, scope):
        # check ilegal redefined func
        self.current_method = self.current_type.get_method(node.id)
        
        scope.define_variable('self', self.current_type)
        
        for pname, ptype in zip(self.current_method.param_names, self.current_method.param_types):
            scope.define_variable(pname, ptype)
            
        self.visit(node.body, scope.create_child())
            
        body_type = node.body.static_type
        return_type = self.current_type if isinstance(self.current_method.return_type, SelfType) else self.current_method.return_type
        
        if not body_type.conforms_to(return_type):
            self.errors.append(INCOMPATIBLE_TYPES % (body_type.name, return_type.name))

    @visitor.when(IfThenElseNode)
    def visit(self, node, scope):
        self.visit(node.condition, scope.create_child())

        condition_type = node.condition.static_type
        if not condition_type.conforms_to(self.bool_type):
            self.errors.append(INCOMPATIBLE_TYPES % (condition_type.name, self.bool_type.name))

        self.visit(node.if_body, scope.create_child())
        self.visit(node.else_body, scope.create_child())

        if_type = node.if_body.static_type
        else_type = node.else_body.static_type
        node.static_type = if_type.type_union(else_type)

    @visitor.when(WhileLoopNode)
    def visit(self, node, scope):
        self.visit(node.condition, scope.create_child())

        condition_type = node.condition.static_type
        if not condition_type.conforms_to(self.bool_type):
            self.errors.append(INCOMPATIBLE_TYPES % (condition_type.name, self.bool_type.name))

        self.visit(node.body, scope.create_child())

        node.static_type = self.object_type

    @visitor.when(BlockNode)
    def visit(self, node, scope):
        for expr in node.expressions:
            self.visit(expr, scope.create_child())

        node.static_type = node.expressions[-1].static_type

    @visitor.when(LetInNode)
    def visit(self, node, scope):
        child_scope = scope.create_child()

        for idx, typex, expr in node.let_body:
            try:
                node_type = self.context.get_type(typex)
            except SemanticError as ex:
                self.errors.append(ex.text)
                node_type = ErrorType()
            
            id_type = self.current_type if isinstance(node_type, SelfType) else node_type

            if expr:
                self.visit(expr, child_scope.create_child())
                expr_type = expr.static_type
                if not expr_type.conforms_to(id_type):
                    self.errors.append(INCOMPATIBLE_TYPES % (expr_type.name, id_type.name))

            child_scope.define_variable(idx, id_type)

        self.visit(node.in_body, child_scope)

        node.static_type = node.in_body.static_type

    @visitor.when(CaseOfNode)
    def visit(self, node, scope):
        self.visit(node.expression, scope.create_child())

        node.static_type = None

        for idx, typex, expr in node.branches:
            try:
                node_type = self.context.get_type(typex)
            except SemanticError as ex:
                self.errors.append(ex.text)
                node_type = ErrorType()

            id_type = self.current_type if isinstance(node_type, SelfType) else node_type

            child_scope = scope.create_child()
            child_scope.define_variable(idx, id_type)
            self.visit(expr, child_scope)
            expr_type = expr.static_type

            node.static_type = node.static_type.type_union(expr_type) if node.static_type else expr_type

    @visitor.when(AssignNode)
    def visit(self, node, scope):
        self.visit(node.expression, scope.create_child())
        expr_type = node.expression.static_type
        
        if scope.is_defined(node.id):
            var = scope.find_variable(node.id)
            node_type = var.type       
            
            if var.name == 'self':
                self.errors.append(SELF_IS_READONLY)
            elif not expr_type.conforms_to(node_type):
                self.errors.append(INCOMPATIBLE_TYPES % (expr_type.name, node_type.name))
        else:
            self.errors.append(VARIABLE_NOT_DEFINED % (node.id, self.current_method.name))
        
        node.static_type = expr_type

    @visitor.when(NotNode)
    def visit(self, node, scope):
        self.visit(node.expression, scope.create_child())

        expr_type = node.expression.static_type
        if not expr_type.conforms_to(self.bool_type):
            self.errors.append(INCOMPATIBLE_TYPES % (expr_type.name, self.bool_type.name))

        node.static_type = self.bool_type

    @visitor.when(LessEqualNode)
    def visit(self, node, scope):
        self.visit(node.left, scope.create_child())

        left_type = node.left.static_type
        if not left_type.conforms_to(self.int_type):
            self.errors.append(INVALID_OPERATION % (left_type.name, self.int_type.name))

        self.visit(node.right, scope.create_child())

        right_type = node.right.static_type
        if not right_type.conforms_to(self.int_type):
            self.errors.append(INVALID_OPERATION % (right_type.name, self.int_type.name))

        node.static_type = self.bool_type

    @visitor.when(LessNode)
    def visit(self, node, scope):
        self.visit(node.left, scope.create_child())

        left_type = node.left.static_type
        if not left_type.conforms_to(self.int_type):
            self.errors.append(INVALID_OPERATION % (left_type.name, self.int_type.name))

        self.visit(node.right, scope.create_child())

        right_type = node.right.static_type
        if not right_type.conforms_to(self.int_type):
            self.errors.append(INVALID_OPERATION % (right_type.name, self.int_type.name))

        node.static_type = self.bool_type

    @visitor.when(EqualNode)
    def visit(self, node, scope):
        self.visit(node.left, scope.create_child())
        left_type = node.left.static_type

        self.visit(node.right, scope.create_child())
        right_type = node.right.static_type

        if left_type.conforms_to(self.int_type) ^ right_type.conforms_to(self.int_type):
            self.errors.append(INVALID_OPERATION % (left_type.name, right_type.name))

        if left_type.conforms_to(self.string_type) ^ right_type.conforms_to(self.string_type):
            self.errors.append(INVALID_OPERATION % (left_type.name, right_type.name))

        if left_type.conforms_to(self.bool_type) ^ right_type.conforms_to(self.bool_type):
            self.errors.append(INVALID_OPERATION % (left_type.name, right_type.name))

        node.static_type = self.bool_type
    
    @visitor.when(ArithmeticNode)
    def visit(self, node, scope):
        self.visit(node.left, scope.create_child())
        left_type = node.left.static_type
        
        self.visit(node.right, scope.create_child())
        right_type = node.right.static_type
        
        if not left_type.conforms_to(self.int_type) or not right_type.conforms_to(self.int_type):
            self.errors.append(INVALID_OPERATION % (left_type.name, right_type.name))
            
        node.static_type = self.int_type

    @visitor.when(IsVoidNode)
    def visit(self, node, scope):
        self.visit(node.expression, scope.create_child())

        node.static_type = self.bool_type

    @visitor.when(ComplementNode)
    def visit(self, node, scope):
        self.visit(node.expression, scope.create_child())

        expr_type = node.expression.static_type
        if not expr_type.conforms_to(self.int_type):
            self.errors.append(INCOMPATIBLE_TYPES % (expr_type.name, self.int_type.name))

        node.static_type = self.int_type

    @visitor.when(FunctionCallNode)
    def visit(self, node, scope):
        self.visit(node.obj, scope.create_child())
        obj_type = node.obj.static_type
        
        try:
            if node.type:
                try:
                    node_type = self.context.get_type(node.type)
                except SemanticError as ex:
                    self.errors.append(ex.text)
                    node_type = ErrorType()

                if not obj_type.conforms_to(node_type):
                    self.errors.append(INCOMPATIBLE_TYPES % (obj_type.name, node_type.name))
                obj_type = node.type
            
            obj_method = obj_type.get_method(node.id)
            
            if len(node.args) == len(obj_method.param_types):
                for arg, param_type in zip(node.args, obj_method.param_types):
                    self.visit(arg, scope.create_child())
                    arg_type = arg.static_type
                    
                    if not arg_type.conforms_to(param_type):
                        self.errors.append(INCOMPATIBLE_TYPES % (arg_type.name, param_type.name))
            else:
                self.errors.append(f'Method "{obj_method.name}" of "{obj_type.name}" only accepts {len(obj_method.param_types)} argument(s)')
            
            node_type = obj_type if isinstance(obj_method.return_type, SelfType) else obj_method.return_type
        except SemanticError as ex:
            self.errors.append(ex.text)
            node_type = ErrorType()
            
        node.static_type = node_type

    @visitor.when(MemberCallNode)
    def visit(self, node, scope):
        obj_type = self.current_type
        
        try:
            obj_method = obj_type.get_method(node.id)
            
            if len(node.args) == len(obj_method.param_types):
                for arg, param_type in zip(node.args, obj_method.param_types):
                    self.visit(arg, scope.create_child())
                    arg_type = arg.static_type
                    
                    if not arg_type.conforms_to(param_type):
                        self.errors.append(INCOMPATIBLE_TYPES % (arg_type.name, param_type.name))
            else:
                self.errors.append(f'Method "{obj_method.name}" of "{obj_type.name}" only accepts {len(obj_method.param_types)} argument(s)')
            
            node_type = obj_type if isinstance(obj_method.return_type, SelfType) else obj_method.return_type
        except SemanticError as ex:
            self.errors.append(ex.text)
            node_type = ErrorType()
            
        node.static_type = node_type

    @visitor.when(NewNode)
    def visit(self, node, scope):
        try:
            node_type = self.context.get_type(node.type)
        except SemanticError as ex:
            self.errors.append(ex.text)
            node_type = ErrorType()
            
        node.static_type = node_type

    @visitor.when(IntegerNode)
    def visit(self, node, scope):
        node.static_type = self.int_type

    @visitor.when(StringNode)
    def visit(self, node, scope):
        node.static_type = self.string_type

    @visitor.when(IdNode)
    def visit(self, node, scope):
        if scope.is_defined(node.lex):
            var = scope.find_variable(node.lex)
            node_type = var.type       
        else:
            self.errors.append(VARIABLE_NOT_DEFINED % (node.lex, self.current_method.name))
            node_type = ErrorType()
        
        node.static_type = node_type
    
    @visitor.when(BoolNode)
    def visit(self, node, scope):
        node.static_type = self.bool_type


class FormatVisitor(object):
    @visitor.on('node')
    def visit(self, node, tabs):
        pass
    
    @visitor.when(ProgramNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__ProgramNode [<class> ... <class>]'
        statements = '\n'.join(self.visit(child, tabs + 1) for child in node.declarations)
        return f'{ans}\n{statements}'
    
    @visitor.when(ClassDeclarationNode)
    def visit(self, node, tabs=0):
        parent = '' if node.parent is None else f"inherits {node.parent}"
        ans = '\t' * tabs + f'\\__ClassDeclarationNode: class {node.id} {parent} {{ <feature> ... <feature> }}'
        features = '\n'.join(self.visit(child, tabs + 1) for child in node.features)
        return f'{ans}\n{features}'
    
    @visitor.when(AttrDeclarationNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__AttrDeclarationNode: {node.id}: {node.type}' + ('<- <expr>' if node.expression else '')
        expr = node.visit(node.expr, tabs + 1) if node.expression else None
        return f'{ans}' + (f'\n{expr}' if expr else '')
    
    @visitor.when(FuncDeclarationNode)
    def visit(self, node, tabs=0):
        params = ', '.join(': '.join(param) for param in node.params)
        ans = '\t' * tabs + f'\\__FuncDeclarationNode: {node.id}({params}): {node.type} {{ <expr> }}'
        body = self.visit(node.body, tabs + 1)
        return f'{ans}\n{body}'

    @visitor.when(IfThenElseNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\_IfThenElseNode: if <expr> then <expr> else <expr> fi'
        cond = self.visit(node.condition, tabs + 1)
        if_body = self.visit(node.if_body, tabs + 1)
        else_body = self.visit(node.else_body, tabs + 1)
        return f'{ans}\n{cond}\n{if_body}\n{else_body}'

    @visitor.when(WhileLoopNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\_WhileNode: while <expr> loop <expr> pool'
        cond = self.visit(node.condition, tabs + 1)
        body = self.visit(node.body, tabs + 1)
        return f'{ans}\n{cond}\n{body}'

    @visitor.when(BlockNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\_BlockNode: {{ <expr>; ... <expr>; }}'
        expressions = '\n'.join(self.visit(expr, tabs + 1) for expr in node.expressions)
        return f'{ans}\n{expressions}'

    @visitor.when(LetInNode)
    def visit(self, node, tabs=0):
        let_body = ', '.join(f'{idx}: {typex}' + (' <- <expr>' if expr else '') for idx, typex, expr in node.let_body)
        ans = '\t' * tabs + f'\\_LetInNode: let {let_body} in <expr>'
        lets = '\n'.join(self.visit(expr, tabs + 1) for _, _, expr in node.let_body if expr)
        body = self.visit(node.in_body, tabs + 1)
        return f'{ans}\n{lets}\n{body}'

    @visitor.when(CaseOfNode)
    def visit(self, node, tabs=0):
        case_body = ' '.join(f'{idx}: {typex} => <expr>;' for idx, typex, expr in node.branches)
        ans = '\t' * tabs + f'\\_CaseOfNode: case <expr> of {case_body} esac'
        expression = self.visit(node.expression, tabs + 1)
        body = '\n'.join(self.visit(expr, tabs + 1) for _, _, expr in node.branches)
        return f'{ans}\n{expression}\n{body}'

    @visitor.when(AssignNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\_AssingNode: {node.id} <- <expr>'
        expr = self.visit(node.expression, tabs + 1)
        return f'{ans}\n{expr}'

    @visitor.when(UnaryNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__{node.__class__.__name__} <expr>'
        expression = self.visit(node.expression, tabs + 1)
        return f'{ans}\n{expression}'

    @visitor.when(BinaryNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__<expr> {node.__class__.__name__} <expr>'
        left = self.visit(node.left, tabs + 1)
        right = self.visit(node.right, tabs + 1)
        return f'{ans}\n{left}\n{right}'    

    @visitor.when(FunctionCallNode)
    def visit(self, node, tabs=0):
        obj = self.visit(node.obj, tabs + 1)
        typex = f'@{node.type}' if node.type else ''
        ans = '\t' * tabs + f'\\__FunctionCallNode: <obj>{typex}.{node.id}(<expr>, ..., <expr>)'
        args = '\n'.join(self.visit(arg, tabs + 1) for arg in node.args)
        return f'{ans}\n{obj}\n{args}'

    @visitor.when(MemberCallNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__MemberCallNode: {node.id}(<expr>, ..., <expr>)'
        args = '\n'.join(self.visit(arg, tabs + 1) for arg in node.args)
        return f'{ans}\n{args}'
    
    @visitor.when(NewNode)
    def visit(self, node, tabs=0):
        return '\t' * tabs + f'\\__ NewNode: new {node.type}'

    @visitor.when(AtomicNode)
    def visit(self, node, tabs=0):
        return '\t' * tabs + f'\\__ {node.__class__.__name__}: {node.lex}'

tokens_dict = {
    'CLASS': CoolGrammar['class'],
	'INHERITS': CoolGrammar['inherits'],
	'IF': CoolGrammar['if'],
	'THEN': CoolGrammar['then'],
	'ELSE': CoolGrammar['else'],
	'FI': CoolGrammar['fi'],
	'WHILE': CoolGrammar['while'],
	'LOOP': CoolGrammar['loop'],
	'POOL': CoolGrammar['pool'],
	'LET': CoolGrammar['let'],
	'IN': CoolGrammar['in'],
	'CASE': CoolGrammar['case'],
	'OF': CoolGrammar['of'],
	'ESAC': CoolGrammar['esac'],
	'NEW': CoolGrammar['new'],
	'ISVOID': CoolGrammar['isvoid'],
    'TYPE': CoolGrammar['type'], 
    'ID': CoolGrammar['id'],
	'INTEGER': CoolGrammar['integer'], 
    'STRING': CoolGrammar['string'], 
    'BOOL': CoolGrammar['bool'],
	'ACTION': CoolGrammar['=>'],
	'ASSIGN': CoolGrammar['<-'], 
    'LESS': CoolGrammar['<'], 
    'LESSEQUAL': CoolGrammar['<='], 
    'EQUAL': CoolGrammar['='], 
    'INT_COMPLEMENT': CoolGrammar['~'], 
    'NOT': CoolGrammar['not'],
    '+': CoolGrammar['+'], 
    '-': CoolGrammar['-'],
    '*': CoolGrammar['*'], 
    '/': CoolGrammar['/'], 
    ':': CoolGrammar[':'], 
    ';': CoolGrammar[';'], 
    '(': CoolGrammar['('], 
    ')': CoolGrammar[')'], 
    '{': CoolGrammar['{'], 
    '}': CoolGrammar['}'], 
    '@': CoolGrammar['@'], 
    '.': CoolGrammar['.'], 
    ',': CoolGrammar[',']
}

def pprint_tokens(tokens):
    ocur, ccur, semi = CoolGrammar['{'], CoolGrammar['}'], CoolGrammar[';']
    indent = 0
    pending = []
    for token in tokens:
        pending.append(token)
        if token.token_type in { ocur, ccur, semi }:
            if token.token_type == ccur:
                indent -= 1
            print('    '*indent + ' '.join(str(t.token_type) for t in pending))
            pending.clear()
            if token.token_type == ocur:
                indent += 1
    print(' '.join([str(t.token_type) for t in pending]))

def run_pipeline(text):
    print('=================== TEXT ======================')
    print(text)
    print('================== TOKENS =====================')
    tokens = [Token(token.value, tokens_dict[token.type]) for token in tokenizer(text)] + [Token('$', CoolGrammar.EOF)]
    pprint_tokens(tokens)
    print('=================== PARSE =====================')
    parse, operations = CoolParser([t.token_type for t in tokens])
    print('\n'.join(repr(x) for x in parse))
    print('==================== AST ======================')
    ast = evaluate_reverse_parse(parse, operations, tokens)
    formatter = FormatVisitor()
    tree = formatter.visit(ast)
    print(tree)
    print('============== COLLECTING TYPES ===============')
    errors = []
    collector = TypeCollector(errors)
    collector.visit(ast)
    context = collector.context
    print('Errors:', errors)
    print('Context:')
    print(context)
    print('=============== BUILDING TYPES ================')
    builder = TypeBuilder(context, errors)
    builder.visit(ast)
    print('Errors: [')
    for error in errors:
        print('\t', error)
    print(']')
    print('Context:')
    print(context)
    print('=============== CHECKING TYPES ================')
    checker = TypeChecker(context, errors)
    scope = checker.visit(ast)
    print('Errors: [')
    for error in errors:
        print('\t', error)
    print(']')
    return ast, errors, context, scope

text = '''
class A {
    a: Int <- 3;
    suma(a: Int, b: Int): Int {
        a + b
    };
    b: Int;
};

class B inherits A {
    c: A <- new A;
    f(d: Int, a: A): String { {
        isvoid d;
        f(1, new A);
        let f: Int <- 1 in { 
            8;
            if not 5 <= 20 then f * 34 + ~1 else 43 / f + 12 fi;
        };
        c <- new A.suma(5, f);
        c;
    } };
    z: Bool <- false;
};

class Point {
    x : AUTO_TYPE;
    y : AUTO_TYPE;
    init(n : Int, m : Int) : SELF_TYPE { {
        x <- n;
        y <- m;
        self;
    } };
};

class Main inherits IO {
    main(): Object { {
        out_string("Enter an integer greater-than or equal-to 0: ");

        let input: Int <- in_int() in
        if input < 0 then
            out_string("ERROR: Number must be greater-than or equal-to 0\\n")
        else {
            out_string("The factorial of ").out_int(input);
            out_string(" is ").out_int(factorial(input));
            out_string("\\n");
        }
        fi;
    } };

    test() : AUTO_TYPE {
        let x : AUTO_TYPE <- 3 + 2 in {
            case x of
                y : Int => out_string("Ok");
            esac;
        }
    };

    factorial(num: Int): Int {
        if num = 0 then 1 else num * factorial(num - 1) fi
    };

    ackermann(m : AUTO_TYPE, n: AUTO_TYPE) : AUTO_TYPE {
        if (m=0) then n+1 else
            if (n=0) then ackermann(m-1, 1) else
                ackermann(m-1, ackermann(m, n-1))
            fi
        fi
    };

    f(a: AUTO_TYPE, b: AUTO_TYPE) : AUTO_TYPE {
        if (a=1) then b else
            g(a + 1, b/2)
        fi
    };

    g(a: AUTO_TYPE, b: AUTO_TYPE) : AUTO_TYPE {
        if (b=1) then a else
            f(a/2, b+1)
        fi
    };
};
'''

if __name__ == '__main__':
    run_pipeline(text)