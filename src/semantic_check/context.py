from Type import Type

class Context:
    def __init__(self):
        self.types = {}

    def create_type(self, name:str):
        if name in self.types:
            return [(f'Type with the same name ({name}) already in context.')]   
        self.types[name] = Type(name)
        return []
        
    def get_type(self, name:str):
        try:
            return self.types[name]
        except KeyError:
            return (f'Type "{name}" is not defined.') #arreglar esta historia

    def __str__(self):
        return '{\n\t' + '\n\t'.join(y for x in self.types.values() for y in str(x).split('\n')) + '\n}'

    def __repr__(self):
        return str(self)