class State:
    """Represents a single state in an NFA with a transition table."""
    def __init__(self):
        # Transition table: maps a character (or 'Ɛ') to a list of target states
        self.transitions: dict[str, set[State]] = {}

class accept_state(State):
    """An accepting state that carries the matched token name."""
    def __init__(self, token: str):
        super().__init__()
        self.token = token

class NFA:
    """Represents an NFA with Formal description."""
    def __init__(self, start_state: State, accept_states: list[accept_state],alphabet: list,states: list[State|accept_state]):
        self.alphabet = alphabet
        self.start_State = start_state
        self.accept_States = accept_states
        self.states = states
    
    def δ(self, state: State, char: str) -> list[State]:
        return state.transitions.get(char, [])
    

META_CHARS = {'|', '(', ')', '*', '+', '?', '.'} # Regex operators

def regexes_parser(token_dict:dict):
    for token,regex in token_dict.items():
        



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

def concat_NFAs(NFA1: NFA, NFA2: NFA):
    """Implements concatenation — connects NFA1 and NFA2 in sequence via epsilon-transition."""

    start_State = NFA1.start_State
    accept_State = NFA2.accept_State

    # Demote NFA1's accept and link it to NFA2's start
    NFA1.accept_State.__class__ = State
    del NFA1.accept_State.token
    NFA1.accept_State.add_transition('Ɛ', NFA2.start_State)

    return NFA(start_State, accept_State)


def kleene_NFA(nfa: NFA):
    """Implements '*' (Kleene star) — matches zero or more occurrences."""

    # Skip path: start -> accept (zero occurrences)
    nfa.start_State.add_transition('Ɛ', nfa.accept_State)

    # Loop path: accept -> start (repeat)
    nfa.accept_State.add_transition('Ɛ', nfa.start_State)

    return NFA(nfa.start_State, nfa.accept_State)


def closure_NFA(nfa: NFA):
    """Implements '+' (positive closure) — matches one or more occurrences."""

    # Loop path only
    nfa.accept_State.add_transition('Ɛ', nfa.start_State)

    return NFA(nfa.start_State, nfa.accept_State)


def union_NFAs(nfa1: NFA, nfa2: NFA):
    """Implements '|' — matches either nfa1's or nfa2's pattern."""

    new_start_State = State()

    # point to both start states of the two NFAs
    new_start_State.add_transition('Ɛ', nfa1.start_State)
    new_start_State.add_transition('Ɛ', nfa2.start_State)

    new_accept_State = accept_state(nfa1.accept_State.token)

    # combine the accept states of the two NFAs
    nfa1.accept_State.add_transition('Ɛ', new_accept_State)
    nfa2.accept_State.add_transition('Ɛ', new_accept_State)

    # Demote old accept states so only the new one is accepting
    nfa1.accept_State.__class__ = State
    del nfa1.accept_State.token
    nfa2.accept_State.__class__ = State
    del nfa2.accept_State.token

    new_nfa = NFA(new_start_State, new_accept_State)
    return new_nfa


def optionalNFA(nfa: NFA):
    """Implements '?' — matches zero or one occurrence of the NFA's pattern."""

    new_accepted_state = accept_state(nfa.accept_State.token)

    # ε transitions from the start and old accept state to the new one (ε|"one occurence of the regex") 
    nfa.start_State.add_transition('Ɛ', new_accepted_state)
    nfa.accept_State.add_transition('Ɛ', new_accepted_state)

    # Demote the old accept state to a plain State
    nfa.accept_State.__class__ = State
    del nfa.accept_State.token

    # Return an NFA object
    return NFA(nfa.start_State, new_accepted_state)



def simpleNFA(c: chr, token: str):
    """Builds a 2-state NFA that matches a single character."""

    start_State = State()
    accept_State = accept_state(token)
    start_State.add_transition(c, accept_State)
    
    return NFA(start_State, accept_State)


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