from NFA_to_DFA import regexes_parser, simulate, scan


token_dict:dict[str,str] = {}
with open("src/input.txt", "r") as file:
    for line in file.readlines():
        line = line.strip()
        if not line: continue
        
        # Find quotes to extract token and regex
        first_quote = line.find('"')
        second_quote = line.find('"', first_quote + 1)
        third_quote = line.find('"', second_quote + 1)
        fourth_quote = line.find('"', third_quote + 1)
        
        token = line[first_quote+1:second_quote]
        regex = line[third_quote+1:fourth_quote]
        token_dict[token] = regex

token_list = []
for token in token_dict.keys():
    token_list.append(token)

while True:
    print("--------------------Lexical Analyzer--------------------\n")
    print("\t\t\tOptions"
      "\n\t\t1-Assign Regex to Token"
      "\n\t\t2-Test single input in DFA"
      "\n\t\t3-Scan program input"
      "\n\t\t4-Check current list of Regexs"
      "\n\t\t5-exit"
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
                dfa = regexes_parser(token_dict)
                while True:
                    try:
                        input1:str = input("input tape (-1 to go back):")
                        if input1 == "-1": 
                            break
                        print(simulate(input1,dfa))
                    except Exception:
                        print("invalid input")
            case 3:
                print("Building Regex -> NFA -> DFA...")
                dfa = regexes_parser(token_dict)
                print("Enter program text (type END on a new line to finish):")
                lines = []
                while True:
                    l = input()
                    if l == "END":
                        break
                    lines.append(l)
                program = "\n".join(lines)
                print(f"\n{'Lexeme':<15}{'Token':<15}{'Position'}")
                print("-" * 45)
                scan(program, dfa)
            case 4: 
                for item in token_dict.items():
                    print(item)
            case 5: 
                print("Exiting...")
                with open("src/input.txt", "w") as file:
                    text = []
                    for token,regex in token_dict.items():
                        text.append("(\""+token+"\", \""+regex+"\"),\n")
                    file.write("".join(text))
                break
            case _: "Invalid choice."
    except Exception:
        print("Invalid input.")