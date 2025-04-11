from environment import Env
from abc import ABC
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict, Self, Type
from enum import Enum, auto
from copy import copy, deepcopy
4

class ASTError(Exception):
    pass

class AlphaRenamingError(Exception):
    pass

class SubstitutionError(Exception):
    pass

class AlphaEqError(Exception):
    pass

class BetaReductionError(Exception):
    pass

class TypeInferenceError(Exception):
    pass

def find_fresh_name(name: str, conflicting: Set[str]) -> str:
    i = 1
    while True:
        if name + str(i) not in conflicting: return name + str(i)
        i += 1

@dataclass
class Expr(ABC):
    infered_type: Self | None = None
    def to_str(self) -> str:
        pass
    def get_free_vars(self) -> Set[str]:
        pass
    def naive_alpha_renaming(self, old: str, new: str):
        pass
    def find_unconflicting_subs(self) -> bool:
        pass
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        pass
    def get_type(self, Gamma: Dict[str, Self] = {}) -> Self:
        if self.infered_type is None:
            self.infer_type(Gamma)
        return self.infered_type
    def infer_type(self, Gamma: Dict[str, Self] = {}):
        pass

@dataclass
class Program(Expr):
    program: Expr
    infered_type: Expr | None = None
    def to_str(self) -> str:
        return self.program.to_str()
    def get_free_vars(self) -> Set[str]:
        return self.program.get_free_vars()
    def naive_alpha_renaming(self, old: str, new: str):
        self.program.naive_alpha_renaming(old, new)
    def find_unconflicting_subs(self) -> bool:
        program_last = self.program.find_unconflicting_subs()
        if program_last and isinstance(self.program, Substitution):
            self.program = deepcopy(self.program.do_substitution())
            return False
        return program_last
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str] = {}) -> bool:
        if not isinstance(other, Program): return False
        self_free_vars = self.get_free_vars()
        other_free_vars = other.get_free_vars()
        if self_free_vars != other_free_vars: return False
        var_renaming = dict(zip(self_free_vars, self_free_vars))
        return self.program.alpha_equals(other.program, var_renaming)
    
# id
@dataclass
class Variable(Expr):
    id: str
    infered_type: Expr | None = None
    def to_str(self) -> str:
        return self.id
    def get_free_vars(self) -> Set[str]:
        return {self.id}
    def naive_alpha_renaming(self, old: str, new: str):
        if self.id == old: self.id = new
    def find_unconflicting_subs(self) -> bool:
        return True
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        if not isinstance(other, Variable): return False
        return self.id == var_renaming[other.id]
    
@dataclass
class BetaReduceable(Expr, ABC):
    param: str
    param_type: Expr
    body: Expr
    infered_type: Expr | None = None
    def to_str(self) -> str:
        pass
    def get_free_vars(self) -> Set[str]:
        return (self.body.get_free_vars().union(self.param_type.get_free_vars())) - {self.param}
    def naive_alpha_renaming(self, old: str, new: str):
        self.param_type.naive_alpha_renaming(old, new)
        if self.param != old:
            # self.param_type.naive_alpha_renaming(old, new)
            self.body.naive_alpha_renaming(old, new)
    def find_unconflicting_subs(self) -> bool:
        type_last = self.param_type.find_unconflicting_subs()
        body_last = self.body.find_unconflicting_subs()
        if type_last and isinstance(self.param_type, Substitution):
            self.param_type = deepcopy(self.param_type.do_substitution()) ## deepcopy
            return False
        if body_last and isinstance(self.body, Substitution):
            self.body = deepcopy(self.body.do_substitution()) ## deepcopy
            return False
        return type_last and body_last
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        pass
        

# \id:t.e
@dataclass
class Abstraction(BetaReduceable):
    param: str
    param_type: Expr
    body: Expr
    infered_type: Expr | None = None
    def to_str(self) -> str:
        return f"\\ {self.param}: {self.param_type.to_str()}. {self.body.to_str()}"
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        if not isinstance(other, Abstraction): return False
        type_equals = self.param_type.alpha_equals(other.param_type, var_renaming)
        body_equals = self.body.alpha_equals(other.body, {**var_renaming, other.param : self.param})
        return type_equals and body_equals
        

# #A:B.C
@dataclass
class Product(BetaReduceable):
    param: str
    param_type: Expr
    body: Expr
    infered_type: Expr | None = None
    def to_str(self) -> str:
        return f"& {self.param}: {self.param_type.to_str()}. {self.body.to_str()}"
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        if not isinstance(other, Product): return False
        type_equals = self.param_type.alpha_equals(other.param_type, var_renaming)
        body_equals = self.body.alpha_equals(other.body, {**var_renaming, other.param : self.param})
        return type_equals and body_equals

# f x
@dataclass 
class Application(Expr):
    func: Expr
    arg: Expr
    infered_type: Expr | None = None
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
            self.func = deepcopy(self.func.do_substitution()) ## deepcopy
            return False
        if arg_last and isinstance(self.arg, Substitution):
            self.arg = deepcopy(self.arg.do_substitution()) ## deepcopy
            return False
        return func_last and arg_last
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        if not isinstance(other, Application): return False
        return self.func.alpha_equals(other.func, var_renaming) and self.arg.alpha_equals(other.arg, var_renaming)
    

# e1 [id := e2] with x in FV(e1)
@dataclass
class Substitution(Expr):
    org_expr: Expr
    free_var: str
    sub_expr: Expr
    infered_type: Expr | None = None
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
            # return self.org_expr
            org_abstr = self.org_expr
            return Abstraction(param=org_abstr.param, param_type=Substitution(org_expr=org_abstr.param_type, free_var=self.free_var, sub_expr=self.sub_expr,), body=org_abstr.body)
        elif isinstance(self.org_expr, Abstraction) and self.org_expr.param in self.sub_expr.get_free_vars():
            rename_to = find_fresh_name(self.org_expr.param, self.org_expr.body.get_free_vars().union(self.sub_expr.get_free_vars()).union(self.org_expr.param_type.get_free_vars()))
            self.org_expr.body.naive_alpha_renaming(self.org_expr.param, rename_to)
            #self.org_expr.param_type.naive_alpha_renaming(self.org_expr.param, rename_to)
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
            #self.org_expr.param_type.naive_alpha_renaming(self.org_expr.param, rename_to)
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
            self.org_expr = deepcopy(self.org_expr.do_substitution()) ## deepcopy
            return False
        if sub_last and isinstance(self.sub_expr, Substitution):
            self.sub_expr = deepcopy(self.sub_expr.do_substitution()) ## deepcopy
            return False
        return org_last and sub_last
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        raise AlphaEqError("Substitutions may not be compared")
            

@dataclass
class Universe(Expr, ABC):
    infered_type: Expr | None = None
    def to_str(self) -> str:
        pass
    def get_free_vars(self) -> Set[str]:
        return set()
    def naive_alpha_renaming(self, old: str, new: str):
        return
    def find_unconflicting_subs(self) -> bool:
        return True
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        pass

@dataclass
class Star(Universe):
    infered_type: Expr | None = None
    def to_str(self) -> str:
        return "*"
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        return isinstance(other, Star)

@dataclass
class Square(Universe):
    infered_type: Expr | None = None
    def to_str(self) -> str:
        return "#"
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        return isinstance(other, Square)


SORTS: Set[Type[Universe]] = {Star, Square}
AXIOMS: Set[Tuple[Type[Universe], Type[Universe]]] = {(Star, Square)}
RULES: Set[Tuple[Type[Universe], Type[Universe], Type[Universe]]] = {(Star, Star, Star), (Star, Square, Square), (Square, Star, Star), (Square, Square, Square)}
