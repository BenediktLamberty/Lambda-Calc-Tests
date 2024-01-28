from abstractSyntaxTree import *
from typing import Set, Tuple, Type

SORTS: Set[Type[Universe]] = {Star, Square}
AXIOMS: Set[Tuple[Universe, Universe]] = {(Star, Square)}
RULES: Set[Tuple[Universe, Universe, Universe]] = {(Star, Star, Star), (Star, Square, Square), (Square, Star, Star), (Square, Square, Square)}