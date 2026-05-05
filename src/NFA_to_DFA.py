from regex_to_NFA import NFA,State,accept_State,epsilonClosure,NFA_Builder,combine_NFAs

class DFA:
    """Represents an NFA with Formal description."""
    def __init__(self, initial_State: DFA_State, accept_states: set[DFA_Accept_State],alphabet: set,Q: set[DFA_State|DFA_Accept_State|DFA_Trap_State]):
        self.alphabet = alphabet
        self.initial_State = initial_State
        self.accept_States = accept_states
        self.Q = Q
    
    def δ(self, state: DFA_State, char: str) -> DFA_State:
        return state.transitions.get(char, DFA_Trap_State(frozenset()))

class DFA_State():
    def __init__(self,nfa_states:frozenset):
        self.nfa_states = nfa_states
        self.transitions: dict[str, DFA_State] = {}

    def add_transition(self, char, target_state):
        self.transitions[char] = target_state

class DFA_Accept_State(DFA_State):
    def __init__(self, nfa_states,token:str):
        super().__init__(nfa_states)
        self.token = token

class DFA_Trap_State(DFA_State):
    def __init__(self, nfa_states):
        super().__init__(nfa_states)

def NFA_to_DFA(nfa:NFA,token_list:list[str]):
    #initialze DFA
    initial_state = DFA_State(frozenset(epsilonClosure(nfa.initial_State)))
    dfa = DFA(initial_state, set(), nfa.alphabet, {initial_state}) 

    #2 queues 1 for each set of states and 1 queue to represent each set as a single DFA state
    frozen_queue:list[frozenset[State]] = [epsilonClosure(nfa.initial_State)]
    DFA_states_queue:list[DFA_State] = [initial_state]
    #this is for already proccessed set of states as a signle DFA state
    seen:dict[frozenset, DFA_State] = {frozenset(epsilonClosure(nfa.initial_State)): initial_state}

    #while theres new subsets
    while frozen_queue:
        #parallel queues
        current_set_of_states = frozen_queue.pop(0)
        current_DFA_state = DFA_states_queue.pop(0)
        #iterate over each symbol in the alphabet
        for symbol in nfa.alphabet:
            result:set[State] = set()
            #get the result subset by checking the transition on said symbol through each state in the source subset
            for state in current_set_of_states:
                result.update(nfa.δ(state,symbol))


            closure:set[State] = set()
            for state in result:
                closure.update(epsilonClosure(state))

            flag = ""
            accept_states_tokens_in_closure:list[str] = []
            for state in closure:
                if type(state) is accept_State:
                    flag = "accept"
                    accept_states_tokens_in_closure.append(state.token)

            if flag == "accept":
                #to match accept specefication in the input
                for token in token_list:
                    if token in accept_states_tokens_in_closure:
                         target_DFA_state = DFA_Accept_State(frozenset(closure),token)
                         break
            elif not closure:
                target_DFA_state = DFA_Trap_State(frozenset(closure))
            else:
                target_DFA_state = DFA_State(frozenset(closure))
            if frozenset(closure) not in seen:
                seen[frozenset(closure)] = target_DFA_state
                frozen_queue.append(frozenset(closure))
                DFA_states_queue.append(target_DFA_state)
                if flag == "accept":
                    dfa.accept_States.add(target_DFA_state)
                dfa.Q.add(target_DFA_state)

            current_DFA_state.add_transition(symbol, seen[frozenset(closure)])

    return dfa

def simulate(input_tape:str,dfa:DFA):
    current_state = dfa.initial_State
    for symbol in input_tape:
        current_state = dfa.δ(current_state,symbol)
        if type(current_state) is DFA_Trap_State: return "rejected"
    if type(current_state) is DFA_Accept_State:
        return current_state.token
    else:
        return "rejected"


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

def expand_regex(regex: str):
    for key, val in bracket_map.items():
        regex = regex.replace(f"[{key}]", val)
    return regex

def regexes_parser(token_dict:dict):
    nfa_list:list[NFA] = []
    for token,regex in token_dict.items():
        if regex is None: continue
        nfa_list.append(NFA_Builder(expand_regex(regex),token))

    token_list:list[str] = []
    for token in token_dict.keys():
        token_list.append(token)

    return NFA_to_DFA(combine_NFAs(nfa_list),token_list)
