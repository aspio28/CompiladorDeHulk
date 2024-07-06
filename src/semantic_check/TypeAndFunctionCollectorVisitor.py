import utils.visitor as visitor
from  ast_nodes.hulk_ast_nodes import *
from semantic_check.context import Context
from semantic_check.Scope import Scope

class TypeAndFunctionCollector(object):
    def __init__(self, errors=[]):
        self.context = None
        self.scope = None
        self.errors = errors
    
    @visitor.on('node')
    def visit(self, node):
        pass
    
    @visitor.when(ProgramNode)
    def visit(self, node):
        self.context = Context()
        self.scope = Scope()
        
        for definition in node.definitions:
            self.visit(definition)
        
        return self.context, self.scope

    @visitor.when(TypeDefNode)
    def visit(self, node):
        self.errors += self.context.create_type(node.identifier)
    
    @visitor.when(ProtocolDefNode)
    def visit(self, node):
        pass
    
    @visitor.when(FuncDefNode)
    def visit(self, node):
        self.errors += self.scope.define_function(node.identifier, [(param[0], param[1].lex if param[1] else "Object") for param in node.params_list], node.return_type_token.lex if node.return_type_token else "Object")
        