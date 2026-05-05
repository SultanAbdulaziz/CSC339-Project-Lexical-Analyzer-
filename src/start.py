from NFA_to_DFA import regexes_parser,simulate


token_dict:dict[str,str] = {}
with open("input.txt", "r") as file:
    for line in file.readlines():
        line_split = line.split(",")
        token = line_split[0][2:-1]
        regex = line_split[1][2:-2]
        token_dict[token] = regex

token_list = []
for token in token_dict.keys():
    token_list.append(token)



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
                print("Building Regex -> NFA -> DFA...")
                while True:
                    try:
                        dfa = regexes_parser(token_dict)
                        input1:str = input("input tape (-1 to go back):")
                        if input1 == "-1": 
                            break
                        print(simulate(input1,dfa))
                    except Exception:
                        print("invalid input")
            case 3: 
                for item in token_dict.items():
                    print(item)
            case 4: 
                print("Exiting...")
                with open("input.txt", "w") as file:
                    text = []
                    for token,regex in token_dict.items():
                        text.append("(\""+token+"\", \""+regex+"\"),\n")
                    file.write("".join(text))
                break
            case _: "Invalid choice."
    except Exception:
        print("Invalid input.")
