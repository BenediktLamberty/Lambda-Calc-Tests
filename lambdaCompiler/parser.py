from abstractSyntaxTree import *
from lexer import tokenize, Token, TokenType, TokenError
from typing import List, Tuple
from abc import ABC

class Par(ABC): pass
class OpenPar(Par): pass
class ClosePar(Par): pass

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
    #     | lambda
    #     | ( e1 )[ var1 := e2 , var2 := e3 ...]
    #     | ( e )
    #     | < e1, e2 >
    
    def parse_expr(self) -> Expr:
        expr_list: List[Expr|Par] = []
        glob_depth = 0
        while True:
            # Vars
            if self.token_of_type(TokenType.VAR): expr_list.append(Variable(id=self.eat().value))
            # Literals
            elif self.token_of_type(TokenType.INT): expr_list.append(Int(value=int(self.eat().value)))
            elif self.token_of_type(TokenType.FLOAT): expr_list.append(Float(value=float(self.eat().value)))
            elif self.token_of_type(TokenType.CHAR): expr_list.append(Char(value=str(self.eat().value)))
            elif self.token_of_type(TokenType.BOOL): expr_list.append(Bool(value=(self.eat().value == "True")))
            # abstraction
            elif self.token_of_type(TokenType.LAMBDA): expr_list.append(self.parse_abstraction())
            # closing Par
            elif self.token_of_type(TokenType.CLOSE_PAREN):
                if glob_depth <= 0: break
                self.eat()
                expr_list.append(ClosePar())
                glob_depth -= 1
            # Pair
            elif self.token_of_type(TokenType.OPEN_PAIR): expr_list.append(self.parse_pair())
            # sub and open par
            elif self.token_of_type(TokenType.OPEN_PAREN):
                depth = 1
                for token in self.tokens[1:]:
                    if depth == 0:
                        if token.type == TokenType.OPEN_BRACKET: expr_list.append("self.parse_substitution()") # TODO 
                        else: 
                            self.eat()
                            expr_list.append(OpenPar())
                            glob_depth += 1
                        break
                    if token.type == TokenType.OPEN_PAREN: depth += 1
                    elif token.type == TokenType.CLOSE_PAREN: depth -= 1
            else: break
        return self.make_applications(expr_list)
    
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
        bound_var = self.expect(TokenType.VAR, "No metavar name in abstraction").value
        self.expect(TokenType.DOT, "No `.` in abstraction")
        return Abstraction(bound_var=bound_var, body=self.parse_expr())
    
    def parse_pair(self):
        self.expect(TokenType.OPEN_PAIR, "No `<` in pair")
        head = self.parse_expr()
        self.expect(TokenType.COMMA, "No `,` in pair")
        tail = self.parse_expr()
        self.expect(TokenType.CLOSE_PAIR, "No `>` in pair")
        return Pair(head=head, tail=tail)




if __name__ == "__main__":
    src = "(x y z) f (g h i (j)(k (l m)))"
    my_parser = Parser()
    my_parser.tokens = tokenize(src)
    print(my_parser.produce_ast())