class state:
    def __init__(self):
        self.transitions = {}

class NFA:
    def __init__(self,start_state: state,accept_state: state):
        self.start_State = start_state
        self.accept_State = accept_state

def insert_concatsymbol(regex: str):
    new_regex = [""] * len(regex) * 2
    for i in range(len(regex)-1):
        if regex[i] not in ["|","("] and regex[i+1] not in ["|",")","*","+"]:
            new_regex.append(regex[i])
            new_regex.append(".")
        else:
            new_regex.append(regex[i]) 
    new_regex.append(regex[-1])
    return "".join(new_regex)

def regextopostfix(regex: str):
    operations_presedence = {"*":3,"+":3,"?":3,".":2,"|":1}
    regex = insert_concatsymbol(regex)
    result = []
    operators_stack = []

    for c in regex:

        #operand
        if c.isalnum():
            result.append(c)

        #open parenthesis
        elif c == "(": 
            operators_stack.append(c)

        #close parenthesis        
        elif c == ")":
            while operators_stack and operators_stack[-1] != "(":
                 result.append(operators_stack.pop())
            operators_stack.pop()
            
        #operator
        else:
            while len(operators_stack) > 0 and operators_stack[-1] != "(" and operations_presedence[c] <= operations_presedence[operators_stack[-1]]:
                result.append(operators_stack.pop())
            operators_stack.append(c)

    for _ in range(len(operators_stack)):
        result.append(operators_stack.pop())
    
    return "".join(result)

def concatNFAs(NFA1:NFA,NFA2:NFA):
    pass
def kleeneNFA(NFA:NFA):
    pass
def closureNFA(NFA:NFA):
    pass
def unionNFAs(NFA1:NFA,NFA2:NFA):
    pass
def optionalNFA(NFA:NFA):
    pass

def simpleNFA(c: chr):
    start_State = state()
    accept_State = state()
    start_State.transitions = {f"{c}":accept_State}
    NFA(start_State,accept_State)
    return NFA

def epsilonNFA_Builder(regex: str):
    postfix_regex = regextopostfix(regex)
    buffer = []
    unioperators = {
        "*": lambda x: kleeneNFA(x),
        "+": lambda x: closureNFA(x),  
        "?": lambda x: optionalNFA(x),
    }
    bioperators = { 
        ".": lambda x, y: concatNFAs(x, y),
        "|": lambda x, y: unionNFAs(x, y)
    }
    for c in postfix_regex:
        
        if c.isalnum():
            buffer.append(simpleNFA(c))

        elif c in unioperators.keys:
            buffer[-1] = unioperators[c](buffer[-1])

        elif c in bioperators.keys:
            nfa = bioperators[c](buffer[-1],buffer[-2])
            buffer.pop()
            buffer.pop()
            buffer.append(nfa)
    
    return buffer[0]
            

        



print(regextopostfix("ab|bd|cd"))