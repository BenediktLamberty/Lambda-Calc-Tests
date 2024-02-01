from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple

class TokenError(Exception):
    pass

class TokenType(Enum):
    LAMBDA = auto() # \
    PROD = auto() # &
    DOT = auto() # .
    COMMA = auto() # ,
    OFTYPE = auto() # :
    SUB = auto() # :=
    TO = auto() # ->
    VAR = auto()
    OPEN_PAREN = auto()  # (
    CLOSE_PAREN = auto()  # )
    OPEN_BRACE = auto()  # {
    CLOSE_BRACE = auto()  # }
    OPEN_BRACKET = auto()  # [
    CLOSE_BRACKET = auto()  # ]
    STAR = auto() # *
    SQUARE = auto() # #
    EOF = auto() # End of File

@dataclass
class Token:
    value: str
    type: TokenType


def tokenize(sourceCode: str) -> List[Token]:

    def is_skippable(src: str) -> bool:
        return src in [" ", "\n", "\t", "\r"]

    tokens = []
    src = list(sourceCode)

    def str_is(search: str) -> bool:
        return len(search) <= len(src) and "".join(src[:len(search)]) == search
    
    def add_token(token_type: TokenType, pop_len: int = 1):
        tokens.append(Token(''.join(src.pop(0) for _ in range(pop_len)), token_type)) 

    # Alle Tokens fürs ganze File erstellen

    while len(src) > 0:
        if str_is("/*"):
            src.pop(0)
            while (not str_is("*/")):
                src.pop(0)
            src.pop(0)
        elif str_is("//"):
            while len(src) > 0 and src[0] != "\n":
                src.pop(0)
        elif str_is("("): add_token(TokenType.OPEN_PAREN)
        elif str_is(")"): add_token(TokenType.CLOSE_PAREN)
        elif str_is("{"): add_token(TokenType.OPEN_BRACE)
        elif str_is("}"): add_token(TokenType.CLOSE_BRACE)
        elif str_is("["): add_token(TokenType.OPEN_BRACKET)
        elif str_is("]"): add_token(TokenType.CLOSE_BRACKET)
        elif str_is(","): add_token(TokenType.COMMA)
        elif str_is("."): add_token(TokenType.DOT)
        elif str_is("\\"): add_token(TokenType.LAMBDA)
        elif str_is("&"): add_token(TokenType.PROD)
        elif str_is(":="): add_token(TokenType.SUB, pop_len=2)
        elif str_is(":"): add_token(TokenType.OFTYPE)
        elif str_is("*"): add_token(TokenType.STAR)
        elif str_is("#"): add_token(TokenType.SQUARE)
        elif str_is("->"): add_token(TokenType.TO, pop_len=2)
        elif src[0].isalpha():
            ident = ""
            while len(src) > 0 and (src[0].isalpha() or src[0].isdigit() or src[0] in ["_", "$"]):
                ident += src.pop(0)
            tokens.append(Token(ident, TokenType.VAR))
        # skip spaces etc
        elif is_skippable(src[0]):
            src.pop(0)
        else:
            raise TokenError(f"Token Error found at >{src[0]}< during lexing")

    tokens.append(Token("EndOfFile", TokenType.EOF))
    return tokens

def main():
    src = "\\x.x f x [x:=y] 'n' 123 hihi12 *nonononono* \\x.$$mips\nmips$$ <1,2> 1.22 True False #why"
    print(tokenize(src))

if __name__ == "__main__":
    main()
    
