class SemanticError(Exception):
    @property
    def text(self):
        return self.args[0]

class Attribute:
    def __init__(self, name, typex):
        self.name = name
        self.type = typex

    def __str__(self):
        return f'[attrib] {self.name} : {self.type.name};'

    def __repr__(self):
        return str(self)

class Method:
    def __init__(self, name, param_names, params_types, return_type):
        self.name = name
        self.param_names = param_names
        self.param_types = params_types
        self.return_type = return_type

    def __str__(self):
        params = ', '.join(f'{n}:{t.name}' for n,t in zip(self.param_names, self.param_types))
        return f'[method] {self.name}({params}): {self.return_type.name};'

class Type:
    def __init__(self, name:str, sealed=False):
        self.name = name
        self.attributes = []
        self.methods = {}
        self.parent = None
        self.sealed = sealed

    def set_parent(self, parent):
        if self.parent is not None:
            raise SemanticError(f'Parent type is already set for {self.name}.')
        if parent.sealed:
            raise SemanticError(f'Parent type "{parent.name}" is sealed. Can\'t inherit from it.')
        self.parent = parent

    def type_union(self, other:Type):
        if self.name == other.name:
            return self

        t1 = [self]
        while t1[-1] != None:
            t1.append(t1[-1].parent)

        t2 = [other]
        while t2[-1] != None:
            t2.append(t2[-1].parent)

        while t1[-2] == t2[-2]:
            t1.pop()
            t2.pop()

        return t1[-2]

    def get_attribute(self, name:str):
        try:
            return next(attr for attr in self.attributes if attr.name == name)
        except StopIteration:
            if self.parent is None:
                raise SemanticError(f'Attribute "{name}" is not defined in {self.name}.')
            try:
                return self.parent.get_attribute(name)
            except SemanticError:
                raise SemanticError(f'Attribute "{name}" is not defined in {self.name}.')

    def define_attribute(self, name:str, typex):
        try:
            self.get_attribute(name)
        except SemanticError:
            attribute = Attribute(name, typex)
            self.attributes.append(attribute)
            return attribute
        else:
            raise SemanticError(f'Attribute "{name}" is already defined in {self.name}.')

    def get_method(self, name:str):
        try:
            return self.methods[name]
        except KeyError:
            # if self.parent is None:
            #     raise SemanticError(f'Method "{name}" is not defined in {self.name}.')
            # try:
            #     return self.parent.get_method(name)
            # except SemanticError:
            #     raise SemanticError(f'Method "{name}" is not defined in {self.name}.')
            raise SemanticError(f'Method "{name}" is not defined in {self.name}.')

    def define_method(self, name:str, param_names:list, param_types:list, return_type):
        try:
            method = self.get_method(name)
        except SemanticError:
            pass
        else:
            # if method.return_type != return_type or method.param_types != param_types:
            #     raise SemanticError(f'Method "{name}" already defined in {self.name} with a different signature.')
            raise SemanticError(f'Method "{name}" already defined in {self.name}')

        method = self.methods[name] = Method(name, param_names, param_types, return_type)
        return method

    def __str__(self):
        output = f'type {self.name}'
        parent = '' if self.parent is None else f' : {self.parent.name}'
        output += parent
        output += ' {'
        output += '\n\t' if self.attributes or self.methods else ''
        output += '\n\t'.join(str(x) for x in self.attributes)
        output += '\n\t' if self.attributes else ''
        output += '\n\t'.join(str(x) for x in self.methods.values())
        output += '\n' if self.methods else ''
        output += '}\n'
        return output

    def __repr__(self):
        return str(self)


class SelfType(Type):
    def __init__(self):
        Type.__init__(self, 'SELF_TYPE')

    def __eq__(self, other):
        return isinstance(other, SelfType)

class AutoType(Type):
    def __init__(self):
        Type.__init__(self, 'AUTO_TYPE')

    def __eq__(self, other):
        return isinstance(other, Type)

class ErrorType(Type):
    def __init__(self):
        Type.__init__(self, '<error>')

    def __eq__(self, other):
        return isinstance(other, Type)

class VoidType(Type):
    def __init__(self):
        Type.__init__(self, '<void>')

    def __eq__(self, other):
        return isinstance(other, VoidType)

class Context:
    def __init__(self):
        self.types = {}

    def create_type(self, name:str):
        if name in self.types:
            raise SemanticError(f'Type with the same name ({name}) already in context.')
        typex = self.types[name] = Type(name)
        return typex

    def add_type(self, typex):
        if typex.name in self.types:
            raise SemanticError(f'Type with the same name ({name}) already in context.')
        self.types[typex.name] = typex
        return typex

    def get_type(self, name:str):
        try:
            return self.types[name]
        except KeyError:
            raise SemanticError(f'Type "{name}" is not defined.')

    def __str__(self):
        return '{\n\t' + '\n\t'.join(y for x in self.types.values() for y in str(x).split('\n')) + '\n}'

    def __repr__(self):
        return str(self)