from environment import Env
from abc import ABC
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum, auto

class ASTError(Exception):
    pass

@dataclass
class Expr(ABC):
    def to_str(self) -> str:
        pass

# id
@dataclass
class Variable(Expr):
    id: str
    variation: int = 0
    def to_str(self) -> str:
        return self.id + (f"${self.variation}" if self.variation != 0 else "")

# \id:t.e
@dataclass
class Abstraction(Expr):
    param: Variable
    param_type: Expr
    body: Expr
    def to_str(self) -> str:
        return f"\\ {self.param.to_str()} : {self.param_type.to_str()}. {self.body.to_str()}"

# #A:B.C
@dataclass
class Product(Expr):
    param: Variable
    param_type: Expr
    body: Expr
    def to_str(self) -> str:
        return f"# {self.param.to_str()} : {self.param_type.to_str()}. {self.body.to_str()}"

# f x
@dataclass 
class Application(Expr):
    func: Expr
    arg: Expr
    def to_str(self) -> str:
        left = f"({self.func.to_str()})" if isinstance(self.func, (Abstraction, Product)) else self.func.to_str()
        right = f"({self.arg.to_str()})" if isinstance(self.arg, Application) else self.arg.to_str()
        return f"{left} {right}"

# e1 [id := e2] with x in FV(e1)
@dataclass
class Substitution(Expr):
    org_expr: Expr
    free_var: Variable
    sub_expr: Expr
    def to_str(self) -> str:
        return f"({self.org_expr.to_str()})[{self.free_var.to_str()} := {self.sub_expr.to_str()}]"

@dataclass
class Universe(Expr, ABC):
    def to_str(self) -> str:
        pass

@dataclass
class Star(Universe):
    def to_str(self) -> str:
        return "*"

@dataclass
class Square(Universe):
    def to_str(self) -> str:
        return "%"



