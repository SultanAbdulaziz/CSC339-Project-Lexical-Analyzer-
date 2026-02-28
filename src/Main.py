TokenRegex = {
    # Keywords class
    "KW_IF":"if",
    "KW_THEN":"then",
    "KW_ELSE":"else",
    "KW_WHILE":"while",
    "KW_FOR":"for",
    "KW_RETURN":"return",
    "KW_CONTINUE":"continue",
    "KW_BREAK":"break",
    "KW_INT":"int",
    "KW_FLOAT":"float",

    #Identifier class
    "ID":"[A-Za-z][A-Za-z0-9_]*",
    #bLetters+sLetters

    #Number class
    "NUM":"[0-9]+(\.[0-9]+)?",

    #Operators class
    "OP":"+",
}

sLetters = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
bLetters = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
digits = ["0","1","2","3","4","5","6","7","8","9"]
operators = ["+","-","*","/","=","<",">"]
delimiters = ["(",")","{","}","[","]",";",","]