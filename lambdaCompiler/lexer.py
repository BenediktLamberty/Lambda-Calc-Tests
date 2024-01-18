from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple

class TokenError(Exception):
    pass

class TokenType(Enum):
    INT = auto()
    FLOAT = auto()
    CHAR = auto()
    BOOL = auto()
    LAMBDA = auto() # \
    DOT = auto() # .
    COMMA = auto() # ,
    SUB = auto() # :=
    MIPS = auto() # Mips Code
    VAR = auto()
    OPEN_PAREN = auto()  # (
    CLOSE_PAREN = auto()  # )
    OPEN_BRACE = auto()  # {
    CLOSE_BRACE = auto()  # }
    OPEN_BRACKET = auto()  # [
    CLOSE_BRACKET = auto()  # ]
    OPEN_PAIR = auto()  # <
    CLOSE_PAIR = auto()  # >
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

    # Alle Tokens fürs ganze File erstellen

    while len(src) > 0:
        if str_is("*"):
            src.pop(0)
            while (not str_is("*")):
                src.pop(0)
            src.pop(0)
        elif str_is("$$"):
            mips = ""
            src.pop(0)
            src.pop(0)
            while (not str_is("$$")):
                mips += src.pop(0)
            src.pop(0)
            src.pop(0)
            tokens.append(Token(mips, TokenType.MIPS))
        elif str_is("#"):
            while len(src) > 0 and src[0] != "\n":
                src.pop(0)
        elif str_is("'"):
            src.pop(0)
            tokens.append(Token(src.pop(0), TokenType.CHAR))
            if str_is("'"): src.pop(0)
        elif str_is("("):
            tokens.append(Token(src.pop(0), TokenType.OPEN_PAREN))
        elif str_is(")"):
            tokens.append(Token(src.pop(0), TokenType.CLOSE_PAREN))
        elif str_is("{"):
            tokens.append(Token(src.pop(0), TokenType.OPEN_BRACE))
        elif str_is("}"):
            tokens.append(Token(src.pop(0), TokenType.CLOSE_BRACE))
        elif str_is("["):
            tokens.append(Token(src.pop(0), TokenType.OPEN_BRACKET))
        elif str_is("]"):
            tokens.append(Token(src.pop(0), TokenType.CLOSE_BRACE))
        elif str_is("<"):
            tokens.append(Token(src.pop(0), TokenType.OPEN_PAIR))
        elif str_is(">"):
            tokens.append(Token(src.pop(0), TokenType.CLOSE_PAIR))
        elif str_is(","):
            tokens.append(Token(src.pop(0), TokenType.COMMA))
        elif str_is("."):
            tokens.append(Token(src.pop(0), TokenType.DOT))
        elif str_is("\\"):
            tokens.append(Token(src.pop(0), TokenType.LAMBDA))
        elif str_is(":="):
            tokens.append(Token(src.pop(0) + src.pop(0), TokenType.SUB))
        elif str_is("True"):
            src = src[4:]
            tokens.append(Token("True", TokenType.BOOL))
        elif str_is("False"):
            src = src[5:]
            tokens.append(Token("False", TokenType.BOOL))
        else: # Multichar token
            # Num Token
            if src[0].isdigit():
                num = ""
                while len(src) > 0 and src[0].isdigit():
                    num += src.pop(0)
                if str_is("."):
                    num += src.pop(0)
                    while len(src) > 0 and src[0].isdigit():
                        num += src.pop(0)
                    tokens.append(Token(num, TokenType.FLOAT))
                else:
                    tokens.append(Token(num, TokenType.INT))
            # ident token
            elif src[0].isalpha():
                ident = ""
                while len(src) > 0 and (src[0].isalpha() or src[0].isdigit()):
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
    
