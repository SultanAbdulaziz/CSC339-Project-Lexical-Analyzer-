token_list = ["KW_IF","KW_THEN","KW_ELSE","KW_WHILE","KW_FOR","KW_RETURN","KW_CONTINUE","KW_BREAK","KW_INT","KW_FLOAT",
              "ID","NUM","EQ","NEQ","LEQ","GEQ","ASSIGN","LT","GT","OP_PLUS","OP_MINUS","OP_MUL","OP_DIV"
                  "LPAREN","RPAREN","LBRACE","RBRACE","SEMI","COMMA"]
token_dict = dict.fromkeys(token_list)

while True:
    print("--------------------Lexical Analyzer--------------------\n")
    print("\t\t\tOptions"
      "\n\t\t1-Assign Regex to Token"
      "\n\t\t2-test input in DFA"
      "\n\t\t3-Check current list of Regexs"
      "\n\t\t4-exit"
      "\n--------------------------------------------------------")

    try:
        choice: int = int(input())
        match choice:
            case 1:
                while True:
                    try:
                        print("choose from the following Token list (-1 to return):\n")
                        for i in range(len(token_list)):
                            print(f"{i+1}. {token_list[i]}")
                        choice2: int = int(input())
                        if choice2 == -1: break
                        token_name = token_list[choice2-1]
                        if token_dict[token_name] is not None:
                            choice3 = input(f"Token already assigned to Regex: {token_dict[token_name]}\nReassign (-1 to go back): ")
                            if choice3 == "-1": continue
                            token_dict[token_name] = choice3
                        else:
                            token_dict[token_name] = input("Regex: ")
                    except Exception:
                        print("invalid input")
            case 2:
                while True:
                    try:
                        print("Building Regex -> NFA -> DFA...")
                    except Exception:
                        print("invalid input")
            case 3: 
                for item in token_dict.items():
                    print(item)
            case 4: 
                print("Exiting...") 
                break
            case _: "Invalid choice."
    except Exception:
        print("Invalid input.")

