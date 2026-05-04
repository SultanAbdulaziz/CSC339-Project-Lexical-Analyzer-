from regex_to_NFA2 import NFA,State,accept_State,epsilonClosure,NFA_Builder

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

def NFA_to_DFA(nfa:NFA):
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
            token = ""
            for state in closure:
                if type(state) is accept_State:
                    flag = "accept"
                    token = state.token

            if flag == "accept":
                target_DFA_state = DFA_Accept_State(frozenset(closure),token)
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

dfa = NFA_to_DFA(NFA_Builder("ab*|h","IF_HL"))
print(simulate("z",dfa))



            

                



        

