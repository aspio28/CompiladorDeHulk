import utils.visitor as visitor
from  ast_nodes.hulk_ast_nodes import *
from utils.error_manager import Not_Defined, Invalid_Argument_Type, Invalid_Initialize_type, Invalid_Operation, Self_Not_Target, Boolean_Expected, Invalid_Arg_Count, Already_Defined, Already_Denfined_In_Type
from semantic_check.Scope import Scope
from semantic_check.context import Context
from semantic_check.utils.Type import Type
class SemeanticChecker(object):
    def __init__(self, errors, context):
        self.errors = errors
        self.context: Context = context
        self.current_type: Type = None
    
    @visitor.on('node')
    def visit(self, node, scope: Scope):
        pass
    
    @visitor.when(ProgramNode)
    def visit(self, node, scope: Scope):
        for definition in node.definitions: 
            self.visit(definition, scope.create_child_scope())                        
            self.current_type = None
            
        self.visit(node.mainExpression, scope)

    @visitor.when(TypeDefNode)
    def visit(self, node: TypeDefNode, scope: Scope):#TODO hecarle un ojo al parent y que no puede heredar de Object, Number, etx..
        self.current_type = self.context.get_type(node.identifier)
        
        print(node.identifier)
        
        
        for param in self.current_type.params:
            if not scope.define_variable(param[0], param[1]):
                self.errors.append(Already_Defined("Parameter", param[1], node.row, node.col))
        for method in self.current_type.methods:
            scope.define_function(method.name, method.params, method.return_type)
        
        scope.define_variable("self", self.current_type.name)
        
        for definition in node.body:
            self.visit(definition, scope)
        
        return node.identifier
            
    @visitor.when(FuncDefNode)
    def visit(self, node:FuncDefNode, scope: Scope):
        for param in node.params_list:
            if param[1] and not param[1].lex in self.context.types: #TODO arreglar esta vaina
                self.errors.append(Not_Defined("Type", param[1].lex, param[1].row, param[1].column))
            if not scope.define_variable(param[0], param[1]):
                self.errors.append(Already_Denfined_In_Type("Param", param[0], node.identifier, param[1].row, param[1].col))
        
        if node.return_type_token and not node.return_type_token.lex in self.context.types: #TODO arreglar esta vaina
                self.errors.append(Not_Defined("Type", node.return_type_token.lex, node.return_type_token.row, node.return_type_token.column))        
        
        base = scope.get_function(node.identifier) #TODO Esto no me cuadra
        
        #TODO buscar si existe base en el arbol de tipos
        
        if self.current_type and self.current_type.get_method(node.identifier, len(node.params_list), node.return_type_token.lex if node.return_type_token else "Object", False):
            scope.define_function("base", base.params, base.return_type)
        
        self.visit(node.body, scope)

    @visitor.when(BlockExprNode)
    def visit(self, node, scope):
        for i, expr in enumerate(node.expr_list):
            expr_type = self.visit(expr, scope)

            if i == len(node.expr_list) - 1:
                return expr_type
            
    @visitor.when(LetInNode)
    def visit(self, node, scope):
        inner_scope = scope.create_child_scope()
        
        for var in node.var_list: 
            self.visit(var, inner_scope)
            
        return self.visit(node.body, inner_scope)
    
    @visitor.when(VarDefNode)
    def visit(self, node:VarDefNode, scope:Scope):
        if not scope.define_variable(node.identifier, node.vtype_token.lex if node.vtype_token else "Object", check=False):
            self.errors.append()
        
        expr_type = self.context.get_type(self.visit(node.expr, scope))

        
        if node.identifier == "self":
            scope.is_self_asignable = True
        
        if node.vtype_token:
            if not node.vtype_token.lex in self.context.types: #TODO arreglar esta vaina
                self.errors.append(Not_Defined("Type", node.vtype_token.lex, node.vtype_token.row, node.vtype_token.column))
                
            if not expr_type.conformed_by(node.vtype_token.lex):
                if self.context.is_protocol_defined(node.vtype_token.lex):
                    protocol = self.context.get_protocol(node.vtype_token.lex)
                    if not expr_type.implements(protocol):
                        self.errors.append(Invalid_Initialize_type(node.identifier, node.vtype_token.lex, expr_type.name, node.expr.row, node.expr.col))
                else:
                    self.errors.append(Invalid_Initialize_type(node.identifier, node.vtype_token.lex, expr_type.name, node.expr.row, node.expr.col))
                    
            return node.vtype_token.lex
        else:
            scope.get_variable(node.identifier).vtype = expr_type.name
            return expr_type.name
            
    @visitor.when(IfElseNode)
    def visit(self, node, scope):
        for expr in node.boolExpr_List:
            expr_type = self.visit(expr, scope)
            if expr_type != "Boolean":
                self.errors.append(Boolean_Expected(expr_type, node.row, node.col))

        #TODO LCA d estos panas
        for expr in node.body_List:
            self.visit(expr, scope)
        
    @visitor.when(WhileLoopNode)
    def visit(self, node, scope):
        condition_type = self.visit(node.condition, scope)
        if condition_type != "Boolean":
            self.errors.append(Boolean_Expected(condition_type, node.condition.row, node.condition.col))

        return self.visit(node.body, scope) #TODO esta vaina tiene q retornar lo de la ultima iteracion o None
    
    @visitor.when(BinaryOperationNode)
    def visit(self, node, scope):
        left_type = self.visit(node.left, scope)
        right_type = self.visit(node.right, scope)

        if node.operator in ['+', '-', '*', '/', '^', '**']:
            if not (left_type == "Number" and right_type == "Number"):
                self.errors.append(Invalid_Operation(node.operator, left_type, right_type, node.row, node.col))
            return "Number"
        
        elif node.operator in ['@', '@@']:
            if not (left_type in ["Number", "String", "Boolean"] and right_type  in ["Number", "String", "Boolean"]):
                self.errors.append(Invalid_Operation(node.operator, left_type, right_type, node.row, node.col))
            return "String"
    
    @visitor.when(BooleanExprNode)
    def visit(self, node, scope):
        left_type = self.visit(node.left, scope)
        right_type = self.visit(node.right, scope)
        
        if node.operator in ['<', '>', '<=', '>=', '==', '!='] and not (left_type == "Number" and right_type == "Number"):
                self.errors.append(Invalid_Operation(node.operator, left_type, right_type, node.row, node.col))
        elif node.operator in ['&', '|'] and not (left_type == "Boolean" and right_type == "Boolean"):
                self.errors.append(Invalid_Operation(node.operator, left_type, right_type, node.row, node.col))

        return "Boolean"
    
    @visitor.when(VarReAsignNode)
    def visit(self, node, scope):
        message = [] #TODO 
        
        if not self.is_self_asignable and node.identifier == 'self':
            self.errors.append(Self_Not_Target(node.row, node.col))
        else:    
            message = scope.is_variable_defined(node.identifier)
            self.errors += message
        
        expr_type = self.context.get_type(self.visit(node.expr, scope))
        
        if len(message) == 0:
            variable = scope.get_variable(node.identifier)
            
            if not expr_type.conformed_by(variable.vtype):
                if self.context.is_protocol_defined(node.vtype_token.lex):
                    protocol = self.context.get_protocol(variable.vtype)
                    if not expr_type.implements(protocol):
                        self.errors.append(Invalid_Initialize_type(node.identifier, variable.vtype, expr_type.name, node.expr.row, node.expr.col))
                else:
                    self.errors.append(Invalid_Initialize_type(node.identifier, variable.vtype, expr_type.name, node.expr.row, node.expr.col))
            
            return variable.vtype

        return "Object"
            
    @visitor.when(FuncCallNode)
    def visit(self, node: FuncCallNode, scope: Scope):
        name_match, param_match = scope.is_function_defined(node.identifier, len(node.args_list))
        
        if name_match:
            function = scope.get_function(node.identifier)
            
            if not param_match:
                self.errors.append(Invalid_Arg_Count(node.identifier, len(function.params), len(node.args_list, node.row, node.col)))
            else:
                for i, arg in enumerate(node.args_list):
                    arg_type = self.context.get_type(self.visit(arg, scope))
                    if not arg_type.conformed_by(function.params[i][1]):
                        self.errors.append(Invalid_Argument_Type(i, node.identifier, function.params[i][1], arg_type.name, arg.row, arg.col))
            
            return function.return_type
        return "Object"
    
    @visitor.when(AtomicNode)
    def visit(self, node, scope):
        if not node.type in self.context.types: #TODO arreglar esta vaina
            self.errors.append(Not_Defined("Type", node.type, node.row, node.column))
        return node.type
    
    @visitor.when(VariableNode)
    def visit(self, node, scope: Scope):
        if scope.is_variable_defined(node.lex):
            return scope.get_variable(node.lex).vtype
        else:
            self.errors.append(Not_Defined("Variable", node.lex, node.row, node.col))
            
        return "Object" #TODO ver como hacemos con los errores aqui
                
    @visitor.when(NewInstanceNode)
    def visit(self, node:NewInstanceNode, scope: Scope):  
        if self.context.is_type_defined(node.identifier):
            type = self.context.get_type(node.identifier)
            params = type.get_params()
            
            if len(params) != len(node.args_list):
                self.errors.append(Invalid_Arg_Count(node.identifier, len(params), len(node.args_list, node.row, node.col)))
            else:    
                for i, arg in enumerate(node.args_list): 
                    arg_type = self.context.get_type(self.visit(arg, scope))
                    if not arg_type.conformed_by(params[i][1]):
                        self.errors.append(Invalid_Argument_Type(i, node.identifier, params[i][1], arg_type.name, arg.row, arg.col))  
            return type.name
        else:
            self.errors.append(Not_Defined("Type", node.identifier, node.row, node.col))
            
        return "Object"