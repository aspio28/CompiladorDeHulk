from semantic_check.utils.Function import Function
from semantic_check.utils.Variable import Variable

class Type:
    def __init__(self, name:str):
        self.name = name
        self.attributes: list[Variable] = []
        self.methods = []
        self.params = []
        self.parent: Type = None
    
    def define_method(self, name:str, params:list, return_type:str):
        if name in (method.name for method in self.methods):
            return [f'Method "{name}" already defined in {self.name}']

        method = Function(name, params, return_type)
        self.methods.append(method)
        return []
    
    def define_attribute(self, name:str, typex:str):    
        if name in (attribute.name for attribute in self.attributes):
            return [f'Attribute "{name}" already defined in {self.name}']

        attribute = Variable(name, typex)
        self.attributes.append(attribute)
        return []
    
    def get_params(self):
        if len(self.params) == 0 and self.parent:
                return self.parent.get_params()
        return self.params
    
    def __str__(self):
        print(self.parent)
        return f'{self.name}{(" inherits " + self.parent.name) if self.parent else ""} {self.attributes} {self.methods}'
    
    def __rep__(self):
        return __str__()