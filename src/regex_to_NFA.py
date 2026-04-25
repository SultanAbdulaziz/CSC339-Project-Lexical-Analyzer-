"""
regex_to_NFA22.py - Regex to epsilon-NFA construction.

Converts regular expressions into epsilon-NFAs.
Supports: concatenation, union (|), Kleene star (*), plus (+), optional (?),
parentheses for grouping, and escape sequences for literal characters.
"""
import sys

sys.setrecursionlimit(300000)

class State:
    """Represents a single state in an NFA with a transition table."""
    def __init__(self):
        # Transition table: maps a character (or 'Ɛ') to a list of target states
        self.transitions: dict[str, list[State]] = {}

    def add_transition(self, char, target_state):
        """Adds a transition on the given character to the target state."""
        if char not in self.transitions:
            self.transitions[char] = []
        self.transitions[char].append(target_state)

class accept_state(State):
    """An accepting state that carries the matched token name."""
    def __init__(self, token: str):
        super().__init__()
        self.token = token


class NFA:
    """Represents an NFA with a single start state and a single accept state."""
    def __init__(self, start_state: State, accept_state: accept_state):
        self.start_State = start_state
        self.accept_State = accept_state

META_CHARS = {'|', '(', ')', '*', '+', '?', '.'} # Regex operators

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


def epsilonNFA_Builder(regex: str, token: str) -> NFA:
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
    closure = set()
    deque: list[State] = []
    if 'Ɛ' in state.transitions.keys():
        deque = list(state.transitions['Ɛ'])

    while deque:
        item = deque.pop(0)
        closure.add(item)
        if 'Ɛ' in item.transitions.keys():
            for value in item.transitions['Ɛ']:
                if value not in closure:
                    deque.append(value)

    return closure


# nfa = epsilonNFA_Builder("a*b*", "True")
# print(regex_to_postfix(r"ab|bd|cd\+"))