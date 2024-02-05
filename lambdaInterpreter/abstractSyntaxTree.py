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
    def infer_type(self, Gamma: Dict[str, Self]) -> Self:
        pass
    def one_beta_normal_reduction(self, Gamma: Dict[str, Self]) -> bool | Self:
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
            self.program = deepcopy(self.program.do_substitution())
            return False
        return program_last
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str] = {}) -> bool:
        print("al eq")
        if not isinstance(other, Program): return False
        self_free_vars = self.get_free_vars()
        other_free_vars = other.get_free_vars()
        if self_free_vars != other_free_vars: return False
        var_renaming = dict(zip(self_free_vars, self_free_vars))
        return self.program.alpha_equals(other.program, var_renaming)
    def infer_type(self, Gamma: Dict[str, Expr] = {}) -> Expr:
        print("infer type")
        return self.program.infer_type(Gamma)
    def one_beta_normal_reduction(self, Gamma: Dict[str, Expr] = {}) -> bool | Expr:
        print("begin one red step")
        return_value =  self.program.one_beta_normal_reduction(Gamma)
        if isinstance(return_value, bool): return return_value
        self.program = deepcopy(return_value) ## deepcopy
        print("end one red step")
        return True
    def to_beta_normal_form(self, Gamma: Dict[str, Expr] = {}):
        while not self.find_unconflicting_subs(): pass
        while self.one_beta_normal_reduction(Gamma): 
            while not self.find_unconflicting_subs(): pass

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
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        if not isinstance(other, Variable): return False
        return self.id == var_renaming[other.id]
    def infer_type(self, Gamma: Dict[str, Expr]) -> Expr:
        if self.id not in set(Gamma.keys()):
            raise TypeInferenceError("Free Variable in infered typing expr")
        return Gamma[self.id]
    def one_beta_normal_reduction(self, Gamma: Dict[str, Expr]) -> bool | Expr:
        return False
    
@dataclass
class BetaReduceable(Expr, ABC):
    param: str
    param_type: Expr
    body: Expr
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
    def one_beta_normal_reduction(self, Gamma: Dict[str, Expr]) -> bool | Expr:
        param_type_rv = self.param_type.one_beta_normal_reduction(Gamma)
        if isinstance(param_type_rv, Expr): 
            self.param_type = deepcopy(param_type_rv) ## deepcopy
            return True
        elif param_type_rv: return True
        body_rv = self.body.one_beta_normal_reduction({**Gamma, self.param : self.param_type})
        if isinstance(body_rv, Expr): 
            self.body = deepcopy(body_rv) ## deepcopy
            return True
        elif body_rv: return True
        return False
        

# \id:t.e
@dataclass
class Abstraction(BetaReduceable):
    param: str
    param_type: Expr
    body: Expr
    def to_str(self) -> str:
        return f"\\ {self.param}: {self.param_type.to_str()}. {self.body.to_str()}"
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        if not isinstance(other, Abstraction): return False
        type_equals = self.param_type.alpha_equals(other.param_type, var_renaming)
        body_equals = self.body.alpha_equals(other.body, {**var_renaming, other.param : self.param})
        return type_equals and body_equals
    def infer_type(self, Gamma: Dict[str, Expr]) -> Expr:
        body_type = self.body.infer_type({**Gamma, self.param : self.param_type})
        self_type = Program(Product(param=deepcopy(self.param), param_type=deepcopy(self.param_type), body=deepcopy(body_type)))
        self_type.to_beta_normal_form(Gamma) # reduction TODO fishy !!!
        if not isinstance(self_type.infer_type(Gamma), tuple(SORTS)):
            raise TypeInferenceError("Abstraction type is not of type sort")
        return self_type.program
        

# #A:B.C
@dataclass
class Product(BetaReduceable):
    param: str
    param_type: Expr
    body: Expr
    def to_str(self) -> str:
        return f"& {self.param}: {self.param_type.to_str()}. {self.body.to_str()}"
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        if not isinstance(other, Product): return False
        type_equals = self.param_type.alpha_equals(other.param_type, var_renaming)
        body_equals = self.body.alpha_equals(other.body, {**var_renaming, other.param : self.param})
        return type_equals and body_equals
    def infer_type(self, Gamma: Dict[str, Expr]) -> Expr:
        param_type_type = self.param_type.infer_type(Gamma)
        param_type_type_program = deepcopy(Program(param_type_type)) # reduction
        param_type_type_program.to_beta_normal_form(Gamma)
        param_type_type = param_type_type_program.program
        if not isinstance(param_type_type, tuple(SORTS)):
            raise TypeInferenceError("Product param type is not of type sort")
        body_type = self.body.infer_type({**Gamma, self.param : self.param_type})
        body_type_program = deepcopy(Program(body_type)) # reduction
        body_type_program.to_beta_normal_form({**Gamma, self.param : self.param_type})
        body_type = body_type_program.program
        if (type(param_type_type), type(body_type), type(body_type)) not in RULES:
            raise TypeInferenceError("Product type dose not follow rules")
        return body_type

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
            self.func = deepcopy(self.func.do_substitution()) ## deepcopy
            return False
        if arg_last and isinstance(self.arg, Substitution):
            self.arg = deepcopy(self.arg.do_substitution()) ## deepcopy
            return False
        return func_last and arg_last
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        if not isinstance(other, Application): return False
        return self.func.alpha_equals(other.func, var_renaming) and self.arg.alpha_equals(other.arg, var_renaming)
    def infer_type(self, Gamma: Dict[str, Expr]) -> Expr:
        func_type = self.func.infer_type(Gamma)
        func_type_program = deepcopy(Program(func_type)) # reduction
        func_type_program.to_beta_normal_form(Gamma)
        func_type = func_type_program.program
        if not isinstance(func_type, Product):
            raise TypeInferenceError("func type is not a product")
        func_body_type = func_type.body
        func_param_type = func_type.param_type
        arg_type = self.arg.infer_type(Gamma)
        arg_type_program = deepcopy(Program(arg_type)) # reduction
        arg_type_program.to_beta_normal_form(Gamma)
        arg_type = arg_type_program.program
        if not Program(program=deepcopy(func_param_type)).alpha_equals(Program(program=deepcopy(arg_type))):
            raise TypeInferenceError("param and arg type do not match")
        self_type_prog = Program(program=Substitution(org_expr=deepcopy(func_body_type), free_var=deepcopy(func_type.param), sub_expr=deepcopy(self.arg))) # TODO ß reduction
        while not self_type_prog.find_unconflicting_subs(): pass
        return self_type_prog.program
    def one_beta_normal_reduction(self, Gamma: Dict[str, Expr]) -> bool | Expr:
        # if func is abstr or prod => reduce it
        if isinstance(self.func, BetaReduceable):
            # compare types
            param_type = Program(program=deepcopy(self.func.param_type))
            param_type.to_beta_normal_form(Gamma)
            arg_type = Program(program=deepcopy(self.arg).infer_type(Gamma))
            arg_type.to_beta_normal_form(Gamma)
            if not param_type.alpha_equals(arg_type):
                print("-----------------") #####
                print(param_type.to_str()) #####
                print(arg_type.to_str()) #####
                raise BetaReductionError("Param and Arg type are not equal")
            return Substitution(org_expr=self.func.body, free_var=self.func.param, sub_expr=self.arg)
        # if func is not abstr => find an other
        func_rv = self.func.one_beta_normal_reduction(Gamma)
        if isinstance(func_rv, Expr):
            self.func = deepcopy(func_rv) ## deepcopy
            return True
        elif func_rv: return True
        arg_rv = self.arg.one_beta_normal_reduction(Gamma)
        if isinstance(arg_rv, Expr):
            self.arg = deepcopy(arg_rv) ## deepcopy
            return True
        elif arg_rv: return True
        return False



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
    def infer_type(self, Gamma: Dict[str, Self]) -> Self:
        raise TypeInferenceError("Substitutions cannot be typed")
    def one_beta_normal_reduction(self, Gamma: Dict[str, Self]) -> bool | Self:
        raise BetaReductionError("Subs cannot be reduced")
            

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
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        pass
    def infer_type(self, Gamma: Dict[str, Expr]) -> Expr:
        for ax in AXIOMS:
            if isinstance(self, ax[0]): return ax[1]()
        raise TypeInferenceError("Universe has no type")
    def one_beta_normal_reduction(self, Gamma: Dict[str, Expr]) -> bool | Expr:
        return False

@dataclass
class Star(Universe):
    def to_str(self) -> str:
        return "*"
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        return isinstance(other, Star)

@dataclass
class Square(Universe):
    def to_str(self) -> str:
        return "#"
    def alpha_equals(self, other: Self, var_renaming: Dict[str, str]) -> bool:
        return isinstance(other, Square)


SORTS: Set[Type[Universe]] = {Star, Square}
AXIOMS: Set[Tuple[Type[Universe], Type[Universe]]] = {(Star, Square)}
RULES: Set[Tuple[Type[Universe], Type[Universe], Type[Universe]]] = {(Star, Star, Star), (Star, Square, Square), (Square, Star, Star), (Square, Square, Square)}
