from environment import Env
from abc import ABC
from dataclasses import dataclass
from typing import List, Tuple

class ASTError(Exception):
    pass

@dataclass
class Expr(ABC):
    def generate_code(self, env: Env) -> str:
        pass

# \id.e
@dataclass
class Abstraction(Expr):
    bound_var: str
    body: Expr

# \id.$$MIPS$$ (predefined functions)
@dataclass
class MipsAbstr(Expr):
    bound_var: str
    body_mips: str

# f x
@dataclass 
class Application(Expr):
    func: Expr
    arg: Expr

# e1 [id := e2] with x in FV(e1)
@dataclass
class Substitution(Expr):
    org_expr: Expr
    free_var: str
    sub_expr: Expr

# <e1, e2>
@dataclass
class Pair(Expr):
    head: Expr
    tail: Expr

# id
@dataclass
class Variable(Expr):
    id: str

@dataclass
class Literal(Expr, ABC):
    def generate_code(self, env: Env) -> str:
        pass

# predefined number 123
@dataclass
class Int(Literal):
    value: int    

# predefined float 1.23
@dataclass
class Float(Literal):
    value: float

# predefined char 'n'
@dataclass
class Char(Literal):
    value: str

# predefined Bools True/False
@dataclass
class Bool(Literal):
    value: bool