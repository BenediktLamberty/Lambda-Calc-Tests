from environment import Env
from abc import ABC
from dataclasses import dataclass
from typing import List, Tuple, Set
from enum import Enum, auto

class ASTError(Exception):
    pass

class AlphaRenamingError(Exception):
    pass

class SubstitutionError(Exception):
    pass

def find_fresh_name(name: str, conflicting: Set[str]) -> str:
    i = 1
    while True:
        if name + str(i) not in conflicting: return name + str(i)
        i += 1

@dataclass
class Expr(ABC):
    def to_str(self) -> str:
        pass
    def get_free_vars(self) -> Set[str]:
        pass
    def naive_alpha_renaming(self, old: str, new: str):
        pass
    def find_unconflicting_subs(self) -> bool:
        pass

@dataclass
class Program(Expr):
    program: Expr
    def to_str(self) -> str:
        return self.program.to_str()
    def get_free_vars(self) -> Set[str]:
        return self.program.get_free_vars()
    def naive_alpha_renaming(self, old: str, new: str):
        self.program.naive_alpha_renaming(old, new)
    def find_unconflicting_subs(self) -> bool:
        program_last = self.program.find_unconflicting_subs()
        if program_last and isinstance(self.program, Substitution):
            self.program = self.program.do_substitution()
            return False
        return program_last

# id
@dataclass
class Variable(Expr):
    id: str
    def to_str(self) -> str:
        return self.id
    def get_free_vars(self) -> Set[str]:
        return {self.id}
    def naive_alpha_renaming(self, old: str, new: str):
        if self.id == old: self.id = new
    def find_unconflicting_subs(self) -> bool:
        return True

# \id:t.e
@dataclass
class Abstraction(Expr):
    param: str
    param_type: Expr
    body: Expr
    def to_str(self) -> str:
        return f"\\ {self.param} : {self.param_type.to_str()}. {self.body.to_str()}"
    def get_free_vars(self) -> Set[str]:
        return (self.body.get_free_vars().union(self.param_type.get_free_vars())) - {self.param}
    def naive_alpha_renaming(self, old: str, new: str):
        if self.param != old:
            self.param_type.naive_alpha_renaming(old, new)
            self.body.naive_alpha_renaming(old, new)
    def find_unconflicting_subs(self) -> bool:
        type_last = self.param_type.find_unconflicting_subs()
        body_last = self.body.find_unconflicting_subs()
        if type_last and isinstance(self.param_type, Substitution):
            self.param_type = self.param_type.do_substitution()
            return False
        if body_last and isinstance(self.body, Substitution):
            self.body = self.body.do_substitution()
            return False
        return type_last and body_last
        

# #A:B.C
@dataclass
class Product(Expr):
    param: str
    param_type: Expr
    body: Expr
    def to_str(self) -> str:
        return f"# {self.param} : {self.param_type.to_str()}. {self.body.to_str()}"
    def get_free_vars(self) -> Set[str]:
        return (self.body.get_free_vars().union(self.param_type.get_free_vars())) - {self.param}
    def naive_alpha_renaming(self, old: str, new: str):
        if self.param != old:
            self.param_type.naive_alpha_renaming(old, new)
            self.body.naive_alpha_renaming(old, new)
    def find_unconflicting_subs(self) -> bool:
        type_last = self.param_type.find_unconflicting_subs()
        body_last = self.body.find_unconflicting_subs()
        if type_last and isinstance(self.param_type, Substitution):
            self.param_type = self.param_type.do_substitution()
            return False
        if body_last and isinstance(self.body, Substitution):
            self.body = self.body.do_substitution()
            return False
        return type_last and body_last

# f x
@dataclass 
class Application(Expr):
    func: Expr
    arg: Expr
    def to_str(self) -> str:
        left = f"({self.func.to_str()})" if isinstance(self.func, (Abstraction, Product)) else self.func.to_str()
        right = f"({self.arg.to_str()})" if isinstance(self.arg, (Application, Abstraction, Product)) else self.arg.to_str()
        return f"{left} {right}"
    def get_free_vars(self) -> Set[str]:
        return self.func.get_free_vars().union(self.arg.get_free_vars())
    def naive_alpha_renaming(self, old: str, new: str):
        self.func.naive_alpha_renaming(old, new)
        self.arg.naive_alpha_renaming(old, new)
    def find_unconflicting_subs(self) -> bool:
        func_last = self.func.find_unconflicting_subs()
        arg_last = self.arg.find_unconflicting_subs()
        if func_last and isinstance(self.func, Substitution):
            self.func = self.func.do_substitution()
            return False
        if arg_last and isinstance(self.arg, Substitution):
            self.arg = self.arg.do_substitution()
            return False
        return func_last and arg_last

# e1 [id := e2] with x in FV(e1)
@dataclass
class Substitution(Expr):
    org_expr: Expr
    free_var: str
    sub_expr: Expr
    def to_str(self) -> str:
        return f"({self.org_expr.to_str()})[{self.free_var} := {self.sub_expr.to_str()}]"
    def get_free_vars(self) -> Set[str]:
        return (self.org_expr.get_free_vars() - {self.free_var}).union(self.sub_expr.get_free_vars())
    def naive_alpha_renaming(self, old: str, new: str):
        raise AlphaRenamingError("No Substitutions may be alpha renamed")
    def do_substitution(self) -> Expr:
        if isinstance(self.org_expr, Variable): 
            return self.sub_expr if self.org_expr.id == self.free_var else self.org_expr
        elif isinstance(self.org_expr, Application):
            org_app = self.org_expr
            return Application(func=Substitution(org_expr=org_app.func, free_var=self.free_var, sub_expr=self.sub_expr),
                                arg=Substitution(org_expr=org_app.arg, free_var=self.free_var, sub_expr=self.sub_expr))
        elif isinstance(self.org_expr, Abstraction) and self.org_expr.param == self.free_var:
            return self.org_expr
        elif isinstance(self.org_expr, Abstraction) and self.org_expr.param in self.sub_expr.get_free_vars():
            rename_to = find_fresh_name(self.org_expr.param, self.org_expr.body.get_free_vars().union(self.sub_expr.get_free_vars()).union(self.org_expr.param_type.get_free_vars()))
            self.org_expr.body.naive_alpha_renaming(self.org_expr.param, rename_to)
            self.org_expr.param_type.naive_alpha_renaming(self.org_expr.param, rename_to)
            self.org_expr.param = rename_to
            return self
        elif isinstance(self.org_expr, Abstraction):
            org_abstr = self.org_expr
            return Abstraction(param=org_abstr.param,
                                param_type=Substitution(org_expr=org_abstr.param_type, free_var=self.free_var, sub_expr=self.sub_expr,),
                                body=Substitution(org_expr=org_abstr.body, free_var=self.free_var, sub_expr=self.sub_expr))
        elif isinstance(self.org_expr, Product) and self.org_expr.param == self.free_var:
            return self.org_expr
        elif isinstance(self.org_expr, Product) and self.org_expr.param in self.sub_expr.get_free_vars():
            rename_to = find_fresh_name(self.org_expr.param, self.org_expr.body.get_free_vars().union(self.sub_expr.get_free_vars()).union(self.org_expr.param_type.get_free_vars()))
            self.org_expr.body.naive_alpha_renaming(self.org_expr.param, rename_to)
            self.org_expr.param_type.naive_alpha_renaming(self.org_expr.param, rename_to)
            self.org_expr.param = rename_to
            return self
        elif isinstance(self.org_expr, Product):
            org_abstr = self.org_expr
            return Product(param=org_abstr.param,
                                param_type=Substitution(org_expr=org_abstr.param_type, free_var=self.free_var, sub_expr=self.sub_expr,),
                                body=Substitution(org_expr=org_abstr.body, free_var=self.free_var, sub_expr=self.sub_expr))
        elif isinstance(self.org_expr, Substitution):
            raise SubstitutionError("Innermost Substitutions must be appied first")
        elif isinstance(self.org_expr, Universe):
            return self.org_expr
        else:
            raise SubstitutionError(f"No expected instance found, instead {self.org_expr}")
    def find_unconflicting_subs(self) -> bool:
        org_last = self.org_expr.find_unconflicting_subs()
        sub_last = self.sub_expr.find_unconflicting_subs()
        if org_last and isinstance(self.org_expr, Substitution):
            self.org_expr = self.org_expr.do_substitution()
            return False
        if sub_last and isinstance(self.sub_expr, Substitution):
            self.sub_expr = self.sub_expr.do_substitution()
            return False
        return org_last and sub_last
            

@dataclass
class Universe(Expr, ABC):
    def to_str(self) -> str:
        pass
    def get_free_vars(self) -> Set[str]:
        return set()
    def naive_alpha_renaming(self, old: str, new: str):
        return
    def find_unconflicting_subs(self) -> bool:
        return True

@dataclass
class Star(Universe):
    def to_str(self) -> str:
        return "*"

@dataclass
class Square(Universe):
    def to_str(self) -> str:
        return "%"



