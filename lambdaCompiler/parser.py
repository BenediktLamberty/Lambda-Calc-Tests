from abstractSyntaxTree import *
from lexer import tokenize, Token, TokenType, TokenError
from typing import List, Tuple
from abc import ABC
from helperFunctions import *

class Par(ABC): pass
class OpenPar(Par): pass
class ClosePar(Par): pass
class Arrow(Par): pass

class Parser:
    tokens: List[Token] = []

    def eat(self) -> Token:
        return self.tokens.pop(0)
    
    def token_of_type(self, token_type: TokenType) -> bool:
        return self.tokens[0].type == token_type
    
    def expect(self, type: TokenType, err: str) -> Token:
        prev = self.tokens.pop(0)
        if prev ==  None or prev.type != type :
            raise TokenError(f"Error at `{prev}` \n{err}\nExpecting: {type}")
        return prev
    
    def produce_ast(self) -> Program:
        return Program(program=self.parse_expr())
    
    # e ::= var
    #     | e1 e2
    #     | \x:A.B
    #     | #x:A.B
    #     | ( e1 )[ var1 := e2 , var2 := e3 ...]
    #     | ( e )
    #     | * | %
    #     | A -> B # TODO
    
    def parse_expr(self) -> Expr:
        expr_list: List[Expr|Par] = []
        glob_depth = 0
        while True:
            # Vars
            if self.token_of_type(TokenType.VAR): 
                expr_list.append(Variable(self.parse_varname()))
            elif self.token_of_type(TokenType.STAR): 
                self.eat()
                expr_list.append(Star())
            elif self.token_of_type(TokenType.SQUARE): 
                self.eat()
                expr_list.append(Square())
            # abstraction
            elif self.token_of_type(TokenType.LAMBDA): expr_list.append(self.parse_abstraction())
            elif self.token_of_type(TokenType.PROD): expr_list.append(self.parse_product())
            # closing Par
            elif self.token_of_type(TokenType.CLOSE_PAREN):
                if glob_depth <= 0: break
                self.eat()
                expr_list.append(ClosePar())
                glob_depth -= 1
            # open par
            elif self.token_of_type(TokenType.OPEN_PAREN):
                glob_depth += 1
                self.eat()
                expr_list.append(OpenPar())
            elif self.token_of_type(TokenType.TO): expr_list.append(Arrow())
            elif self.token_of_type(TokenType.OPEN_BRACKET):
                self.expect(TokenType.OPEN_BRACKET, "No `[` in sub")
                varname = self.parse_varname()
                self.expect(TokenType.SUB, "no `:=` in sub")
                normal, left = self.split_expr(expr_list)
                expr_list = normal
                expr_list.append(Substitution(org_expr=self.make_applications(left), free_var=varname, sub_expr=self.parse_expr()))
                self.expect(TokenType.CLOSE_BRACKET, "No `]` in sub")
            else: break
        return self.make_applications(expr_list)
    
    def split_expr(self, expr_list: List[Expr|Par]) -> Tuple[Expr, Expr]:
        front = expr_list[:]
        last = []
        depth = 0
        for expr in reversed(front):
            if isinstance(expr, OpenPar): depth -= 1
            elif isinstance(expr, ClosePar): depth += 1
            last.append(front.pop())
            if depth <= 0: break
        return (front, list(reversed(last)))
    
    def make_applications(self, expr_list: List[Expr|Par]) -> Expr:
        if len(expr_list) == 1:
            return expr_list[0]
        if len(expr_list) == 2:
            return Application(func=expr_list[0], arg=expr_list[1])
        if not isinstance(expr_list[-1], ClosePar): 
            return Application(func=self.make_applications(expr_list[:-1]), arg=expr_list[-1])
        depth = 1
        for i, expr in enumerate(reversed(expr_list[:-1])):
            if isinstance(expr, OpenPar): depth -= 1
            elif isinstance(expr, ClosePar): depth += 1
            if depth <= 0:
                if i >= len(expr_list[:-1]) - 1: return self.make_applications(expr_list[1:-1])
                return Application(func=self.make_applications(expr_list[:-2-i]), arg=self.make_applications(expr_list[-1-i : -1]))
        raise TokenError(f"Could not make applications from `{expr_list}`")

    
    def parse_abstraction(self) -> Abstraction:
        self.expect(TokenType.LAMBDA, "No `\` in abstraction")
        bound_var = self.parse_varname()
        self.expect(TokenType.OFTYPE, "No type in abstraction")
        param_type = self.parse_expr()
        self.expect(TokenType.DOT, "No `.` in abstraction")
        return Abstraction(param=bound_var, param_type=param_type, body=self.parse_expr())
    
    def parse_product(self) -> Product:
        self.expect(TokenType.PROD, "No `&` in product")
        bound_var = self.parse_varname()
        self.expect(TokenType.OFTYPE, "No type in product")
        param_type = self.parse_expr()
        self.expect(TokenType.DOT, "No `.` in product")
        return Product(param=bound_var, param_type=param_type, body=self.parse_expr())
    
    def parse_varname(self) -> str:
        return self.expect(TokenType.VAR, "Var expected").value
    


if __name__ == "__main__":
    # 
    src1 = "((\ A : *. \ x : type_id A. x) bool true) [id := \ A : *. \ x : A. x] [type_id := \ C : *. C] [bool := & B : *. & x : B. & y : B. B] [true := \ A : *. \ x : A. \ y : A. x]"
    my_parser1 = Parser()
    my_parser1.tokens = tokenize(src1)
    ast1 = my_parser1.produce_ast()
    while not ast1.find_unconflicting_subs(): pass
    print(ast1.to_str())
    ast1.to_beta_normal_form()
    #ast1.one_beta_normal_reduction({})
    print(ast1.to_str())










# (and true true) [and := \ x : bool. \ y : bool. x bool y false] [true := \ A : *. \ x : A. \ y : A. x] [false := \ A : *. \ x : A. \ y : A. y] [bool := & A : *. & x : A. & y : A. A]