import utils.visitor as visitor
from  ast_nodes.hulk_ast_nodes import *

class FormatVisitor(object):
    @visitor.on('node')
    def visit(self, node, tabs):
        pass
    
    @visitor.when(ProgramNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__ProgramNode [<definition>; ... <definition>;] expr;'
        statements = '\n'.join(self.visit(definition, tabs + 1) for definition in node.definitions)
        return f'{ans}{"\n" + statements if statements else ""}\n{self.visit(node.mainExpression, tabs + 1)}'
    
    @visitor.when(TypeDefNode)
    def visit(self, node, tabs=0):
        params = ', '.join(f'{param[0]}: {param[1]}' for param in node.optional_params)
        base_args = ',\n'.join(f'{self.visit(arg, tabs + 1)}' for arg in node.optional_base_args)
        
        inheritance = f' inherits {node.base_identifier} {"(\n" + base_args + "\n" + "\t" * tabs + ")" if base_args else ""}' if node.base_identifier else ""
        
        ans = '\t' * tabs + f'\\__TypeDefNode: {node.identifier}{"(" + params + ")" if params else ""}{inheritance} {"{ <stat>; ... ;<stat>; }"}'
        body = '\n'.join(f'{self.visit(stat, tabs + 1)}' for stat in node.body)
        return f'{ans}\n{body}'
    
    @visitor.when(ProtocolDefNode)
    def visit(self, node, tabs=0):
        inheritance = f' extends {node.base_identifier}' if node.base_identifier else ""
        
        ans = '\t' * tabs + f'\\__ProtocolDefNode: {node.identifier}{inheritance} {"{ <func-dec>; ... <func-dec>; }"}'
        body = '\n'.join(f'{self.visit(stat, tabs + 1)}' for stat in node.body)
        return f'{ans}\n{body}'
    
    @visitor.when(FuncDecNode)
    def visit(self, node, tabs=0):
        params = ', '.join(f'{param[0]}: {param[1]}' for param in node.params_list)
        ans = '\t' * tabs + f'\\__FuncDecNode: {node.identifier}({params}): {node.return_type_token.lex}'
        return f'{ans}'
    
    #TODO arreglar el formater
    
    @visitor.when(FuncDefNode)
    def visit(self, node, tabs=0):
        params = ', '.join(f'{param[0]}: {param[1]}' for param in node.params_list)
        ans = '\t' * tabs + f'\\__FuncDefNode: {node.identifier}({params}): {node.return_type_token.lex if node.return_type_token else None} -> <expr>'
        body = self.visit(node.body, tabs + 1)
        return f'{ans}\n{body}'
    
    @visitor.when(MethodDefNode)
    def visit(self, node, tabs=0):
        params = ', '.join(f'{param[0]}: {param[1]}' for param in node.params_list)
        ans = '\t' * tabs + f'\\__MethodDefNode: {node.identifier}({params}): {node.return_type_token.lex if node.return_type_token else None} -> <expr>'
        body = self.visit(node.body, tabs + 1)
        return f'{ans}\n{body}'
    
    @visitor.when(BlockExprNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__BlockExprNode {"{<expr>; ... <expr>;}"}'
        expr_list = '\n'.join(self.visit(expr, tabs + 1) for expr in node.expr_list)
        return f'{ans}\n{expr_list}'
    
    @visitor.when(LetInNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__LetInNode: let [<var-def>, ... ,<var-def>] in <expr>'
        var_defs = '\n'.join(self.visit(var_def, tabs + 1) for var_def in node.var_list)
        body = self.visit(node.body, tabs + 1)
        
        return f'{ans}\n{var_defs}\n{body}'
    
    @visitor.when(VarDefNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__VarDefNode: {node.identifier}: {node.vtype_token.lex if node.vtype_token else None} = <expr>'
        expr = self.visit(node.expr, tabs + 1)
        return f'{ans}\n{expr}'
    
    @visitor.when(IfElseNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__IfElseNode: if(<boolean-expr>){"{<expr>}"} elif(<boolean-expr>){"{<expr>}"} ... else{"{<expr>}"}'
        
        conditions = '\n'.join(self.visit(expr[1], tabs + 1) for expr in node.boolExpr_List)
        bodies = '\n'.join(self.visit(expr[1], tabs + 1) for expr in node.body_List)
        
        return f'{ans}\n{"\t" * (tabs + 1)}Conditions:\n{conditions}\n{"\t" * (tabs + 1)}Expressions:\n{bodies}'
    
    @visitor.when(WhileLoopNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__WhileLoopNode: while (<boolean-expr>) -> <expr>'
        condition = self.visit(node.condition, tabs + 1)
        body = self.visit(node.body, tabs + 1)
        return f'{ans}\n{condition}\n{body}'
    
    @visitor.when(BinaryOperationNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__{node.__class__.__name__}: <expr> {node.operator} <expr>'
        left = self.visit(node.left, tabs + 1)
        right = self.visit(node.right, tabs + 1)
        return f'{ans}\n{left}\n{right}'
    
    @visitor.when(VarReAsignNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__VarReAsignNode: {node.identifier} := <expr>'
        expr = self.visit(node.expr, tabs + 1)
        return f'{ans}\n{expr}'
    
    @visitor.when(DotNotationNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__DotNotationNode: <dot-notation-expr>.(id | <func-call>)'
        object = self.visit(node.object, tabs + 1)
        member = self.visit(node.member, tabs + 1)
        return f'{ans}\n{object}\n{member}'
    
    @visitor.when(FuncCallNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__FuncCallNode: {node.identifier}(<expr>, ..., <expr>)'
        args = '\n'.join(self.visit(arg, tabs + 1) for arg in node.args_list)
        
        return f'{ans}{"\n" + args if args else ""}'

    @visitor.when(AtomicNode)
    def visit(self, node, tabs=0):
        return '\t' * tabs + f'\\__{node.__class__.__name__}: {node.lex}'
    
    @visitor.when(ConstantNode)
    def visit(self, node, tabs=0):
        return '\t' * tabs + f'\\__{node.__class__.__name__}: {node.lex}: {node.type}'
    
    @visitor.when(NewInstanceNode)
    def visit(self, node, tabs=0):
        ans = '\t' * tabs + f'\\__NewInstanceNode: {node.identifier}(<expr>, ..., <expr>)'
        args = '\n'.join(self.visit(arg, tabs + 1) for arg in node.args_list)
        
        return f'{ans}{"\n" + args if args else ""}'