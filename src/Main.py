"""
Main.py - Token Definitions and Alphabet

Contains the regular expressions for all valid tokens in the language,
the character alphabet (Sigma), and utility functions for character class expansion.
"""

TokenRegex = {
    # Keywords
    "KW_IF": "if",
    "KW_THEN": "then",
    "KW_ELSE": "else",
    "KW_WHILE": "while",
    "KW_FOR": "for",
    "KW_RETURN": "return",
    "KW_CONTINUE": "continue",
    "KW_BREAK": "break",
    "KW_INT": "int",
    "KW_FLOAT": "float",

    # Identifier
    "ID": "[A-Za-z][A-Za-z0-9_]*",

    # Number (integer or decimal)
    "NUM": "[0-9]+(\\.[0-9]+)?",

    # Operators
    "EQ":       "==",
    "NEQ":      "!=",
    "LEQ":      "<=",
    "GEQ":      ">=",
    "ASSIGN":   "=",
    "LT":       "<",
    "GT":       ">",
    "OP_PLUS":  "\\+",
    "OP_MINUS": "-",
    "OP_MUL":   "\\*",
    "OP_DIV":   "/",

    # Delimiters
    "LPAREN": "\\(",
    "RPAREN": "\\)",
    "LBRACE": "{",
    "RBRACE": "}",
    "SEMI":   ";",
    "COMMA":  ",",
}

sLetters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u",
            "v", "w", "x", "y", "z"]
bLetters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U",
            "V", "W", "X", "Y", "Z"]
digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
operators = ["+", "-", "*", "/", "=", "<", ">", "!"]
delimiters = ["(", ")", "{", "}", ";", ","]

Sigma = sLetters + bLetters + digits + operators + delimiters + ["_", "."]

bracket_map = {
    "0-9": "(" + "|".join(digits) + ")",
    "A-Z": "(" + "|".join(bLetters) + ")",
    "a-z": "(" + "|".join(sLetters) + ")",
    "A-Za-z0-9_": "(" + "|".join(sLetters + bLetters + digits + ['_']) + ")",
    "A-Za-z": "(" + "|".join(sLetters + bLetters) + ")"
}

def change(regex: str) -> str:
    """Expands custom character classes (e.g. [A-Za-z]) into basic OR expressions (e.g. (a|b|...|Z)).
    
    Args:
        regex: The regex string containing bracket notation.
    Returns:
        The fully expanded regex string.
    """
    for key, val in bracket_map.items():
        regex = regex.replace(f"[{key}]", val)
    return regex

ExpandedTokenRegex = {name: change(regex) for name, regex in TokenRegex.items()}