class State:
    """Represents a single state in an NFA with a transition table."""
    def __init__(self):
        self.transitions: dict[str, set[State]] = {}

    def add_transition(self, char, target_state):
        """Adds a transition on the given character to the target state."""
        if char not in self.transitions:
            self.transitions[char] = set()
        self.transitions[char].add(target_state)

class accept_State(State):
    """An accepting state that carries the matched token name."""
    def __init__(self, token: str):
        super().__init__()
        self.token = token

class NFA:
    """Represents an NFA with Formal description."""
    def __init__(self, initial_State: State, accept_states: set[accept_State],alphabet: set,Q: set[State|accept_State]):
        self.alphabet = alphabet
        self.initial_State = initial_State
        self.accept_States = accept_states
        self.Q = Q
    
    def δ(self, state: State, char: str) -> set[State]:
        return state.transitions.get(char, set())

META_CHARS = {'|', '(', ')', '*', '+', '?', '.'} # Regex operators

def regexes_parser(token_dict:dict):
    for token,regex in token_dict.items():
        pass
        #todo

def insert_concat_symbol(regex: str):
    """Inserts explicit '.' for implicit concatenation."""

    new_regex = [""] * len(regex) * 2
    i = 0
    while i < len(regex) - 1:
        # If current char is '\', treat '\X' as one unit (escaped literal)
        if regex[i] == '\\' and i + 1 < len(regex):
            new_regex.append(regex[i])      # append '\'
            new_regex.append(regex[i + 1])  # append the escaped char
            i += 2

            # Check if we need a concat dot after this escaped pair
            if i < len(regex) and regex[i] not in ['|', ')', '*', '+', '?']:
                new_regex.append('.')
            continue

        if regex[i] not in ["|", "("] and regex[i + 1] not in ["|", ")", "*", "+", "?"]:
            new_regex.append(regex[i])
            new_regex.append(".")
        else:
            new_regex.append(regex[i])
        i += 1

    if i < len(regex):
        new_regex.append(regex[-1])
    return "".join(new_regex)

def regex_to_postfix(regex: str):
    """Using the Shunting-yard algorithm to convert regex to postfix"""

    operations_precedence = {"*": 3, "+": 3, "?": 3, ".": 2, "|": 1}
    regex = insert_concat_symbol(regex)
    result = []
    operators_stack = []

    i = 0
    while i < len(regex):

        c = regex[i]

        # Escaped character, treat next char as literal operand
        if c == '\\' and i + 1 < len(regex):
            result.append('\\' + regex[i + 1])
            i += 2
            continue

        # operand
        if c not in META_CHARS:
            result.append(c)

        # open parenthesis
        elif c == "(":
            operators_stack.append(c)

        # close parenthesis
        elif c == ")":
            while operators_stack and operators_stack[-1] != "(":
                result.append(operators_stack.pop())
            operators_stack.pop()

        # operator
        else:
            while len(operators_stack) > 0 and operators_stack[-1] != "(" and operations_precedence[c] <= \
                    operations_precedence[operators_stack[-1]]:
                result.append(operators_stack.pop())
            operators_stack.append(c)

        i += 1

    for _ in range(len(operators_stack)):
        result.append(operators_stack.pop())

    return result

def simpleNFA(c: chr, token: str):
    """Builds a 2-state NFA that matches a single character."""

    initial_State = State()
    accept_state = accept_State(token)
    initial_State.transitions[c] = {accept_state}
    return NFA(initial_State,{accept_state},{c},{initial_State,accept_state})

def concat_NFAs(NFA1: NFA, NFA2: NFA):
    """Implements concatenation — connects NFA1 and NFA2 in sequence via epsilon-transition."""

    initial_state = NFA1.initial_State
    accept_states = NFA2.accept_States

    nfa1_accept = NFA1.accept_States.pop()
    #demote accept_State for NFA1
    nfa1_accept.__class__ = State
    del nfa1_accept.token
    #epsilon transition from acceptState of NFA1 to InitialState NFA2
    nfa1_accept.add_transition('Ɛ',NFA2.initial_State)
    
    return NFA(initial_state, accept_states, NFA1.alphabet.union(NFA2.alphabet), NFA1.Q.union(NFA2.Q).union({initial_state}))

def union_NFAs(NFA1: NFA, NFA2: NFA):
    """Implements '|' — matches either nfa1's or nfa2's pattern."""

    initial_state = State()

    nfa1_acceptstate = NFA1.accept_States.pop()
    nfa2_acceptstate = NFA2.accept_States.pop()

    #create 1 accpet with either the nfa1 or nfa2 accept state token
    accept_state = accept_State(nfa1_acceptstate.token)

    #demote both accept states
    nfa1_acceptstate.__class__ = State
    del nfa1_acceptstate.token
    nfa2_acceptstate.__class__ = State
    del nfa2_acceptstate.token

    nfa1_acceptstate.add_transition('Ɛ',accept_state)
    nfa2_acceptstate.add_transition('Ɛ',accept_state)

    initial_state.add_transition('Ɛ',NFA1.initial_State)
    initial_state.add_transition('Ɛ',NFA2.initial_State)
    return NFA(initial_state,{accept_state},NFA1.alphabet.union(NFA2.alphabet), NFA1.Q.union(NFA2.Q).union({initial_state,accept_state}))

def kleene_NFA(nfa: NFA):
    """Implements '*' (Kleene star) — matches zero or more occurrences."""

    initial_state = State()

    old_acceptstate = nfa.accept_States.pop()

    #create 1 accpet with either the nfa1 or nfa2 accept state token
    new_accept_state = accept_State(old_acceptstate.token)

    #demote both accept states
    old_acceptstate.__class__ = State
    del old_acceptstate.token

    initial_state.add_transition('Ɛ',nfa.initial_State)
    initial_state.add_transition('Ɛ',new_accept_state)
    new_accept_state.add_transition('Ɛ',initial_state)
    old_acceptstate.add_transition('Ɛ',new_accept_state)
    

    return NFA(initial_state,{new_accept_state},nfa.alphabet,nfa.Q.union({initial_state,new_accept_state}))

def closure_NFA(nfa: NFA):
    """Implements '+' (positive closure) — matches one or more occurrences."""
    accept_state = nfa.accept_States.pop()
    accept_state.add_transition('Ɛ', nfa.initial_State)
    nfa.accept_States.add(accept_state)
    return nfa

def optionalNFA(nfa: NFA):
    """Implements '?' — matches zero or one occurrence of the NFA's pattern."""

    old_accept_state = nfa.accept_States.pop()
    new_accept_state = accept_State(old_accept_state.token)

    # ε transitions from the start and old accept state to the new one (ε|"one occurence of the regex") 
    nfa.initial_State.add_transition('Ɛ',new_accept_state)
    old_accept_state.add_transition('Ɛ',new_accept_state)

    # Demote the old accept state to a plain State
    old_accept_state.__class__ = State
    del old_accept_state.token

    # Return an NFA object
    return NFA(nfa.initial_State,{new_accept_state},nfa.alphabet,nfa.Q.union({new_accept_state}))

def NFA_Builder(regex: str, token: str) -> NFA:
    """Builds an epsilon-NFA from a regex string using postfix conversion.
    
    Args:
        regex: The regular expression string (may include escape sequences).
        token: The token name to assign to the accept state.
    Returns:
        An NFA object recognizing the given regex.
    """
    postfix_regex = regex_to_postfix(regex)
    buffer = []
    unioperators = {
        "*": lambda x: kleene_NFA(x),
        "+": lambda x: closure_NFA(x),
        "?": lambda x: optionalNFA(x),
    }
    bioperators = {
        ".": lambda x, y: concat_NFAs(x, y),
        "|": lambda x, y: union_NFAs(x, y)
    }
    for c in postfix_regex:

        if c.startswith('\\'):
            buffer.append(simpleNFA(c[1], token))

        elif c not in META_CHARS:
            buffer.append(simpleNFA(c, token))

        elif c in unioperators.keys():
            buffer[-1] = unioperators[c](buffer[-1])

        elif c in bioperators.keys():
            nfa = bioperators[c](buffer[-2], buffer[-1])
            buffer.pop()
            buffer.pop()
            buffer.append(nfa)

    return buffer[0]

def epsilonClosure(state: State) -> set[State]:
    """Computes all states reachable from the given state via epsilon-transitions using BFS.
    
    Args:
        state: The starting NFA state.
    Returns:
        A set of all states reachable via one or more epsilon-transitions.
    """
    stack:list[State] = list(state.transitions.get('Ɛ',[]))
    closure:set[State] = {state}
    while stack:
        state = stack.pop()
        for target_state in state.transitions.get('Ɛ',set()):
            if target_state not in closure:
                stack.append(target_state)
                closure.add(target_state)
        closure.add(state)
    
    return closure