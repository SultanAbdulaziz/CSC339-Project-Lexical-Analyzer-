"""
NFA_to_DFA.py - Subset Construction and DFA Simulation

Converts combined epsilon-NFAs into Deterministic Finite Automata (DFAs)
using the subset construction algorithm, while respecting token matching priority.
"""
from regex_to_NFA22 import NFA, accept_state, State, epsilonClosure,epsilonNFA_Builder
from Main import *


class DFAstate:
    """Represents a DFA state as a frozenset of NFA states."""
    def __init__(self, nfa_states, token_list=None):
        self.nfa_states = frozenset(nfa_states)
        self.transitions: dict[str, 'DFAstate'] = {}

        # Collect all accept states
        accepts = [s for s in nfa_states if isinstance(s, accept_state)]

        if not accepts:
            self.token = None
        elif token_list is not None:
            # Highest priority (lowest index in the specification list)
            self.token = min(accepts, key=lambda s: token_list.index(s.token)).token
        else:
            self.token = accepts[0].token

def build_combined_NFA(token_regex: dict) -> tuple:
    """Builds a combined NFA from all token specifications.
    
    Args:
        token_regex: Ordered dict of {token_name: regex_pattern}.
    Returns:
        (combined_nfa, token_list) where token_list is the priority-ordered token names.
    """    
    token_list = list(token_regex.keys())
    
    # Build individual NFAs
    token_nfas = []
    for token_name, regex in token_regex.items():
        nfa = epsilonNFA_Builder(regex, token_name)
        token_nfas.append(nfa)
    
    # Combine all
    master_start = State()
    for nfa in token_nfas:
        master_start.add_transition('Ɛ', nfa.start_State)
    
    # The NFA constructor requires an accept state (maybe change it later),
    # so we pass the first NFA's accept as a placeholder (the real accept states are all inside the individual NFAs)
    combined_nfa = NFA(master_start, token_nfas[0].accept_State)
    
    return combined_nfa, token_list

def e_close(states):
    """Computes the epsilon-closure for a collection of NFA states.
    
    Args:
        states: An iterable of NFA State objects.
    Returns:
        A frozenset containing the original states and all states reachable 
        via epsilon-transitions.
    """
    states = list(states)
    result = set(states)
    for s in states:
        result |= epsilonClosure(s)
    return frozenset(result)


def NFA_to_DFA(nfa: NFA, token_list=None):
    """Converts an NFA to a DFA using subset construction.
    
    Args:
        nfa: The NFA to convert (can be a combined master NFA).
        token_list: Ordered list of token names for priority resolution.
    Returns:
        The DFA start state.
    """

    start = DFAstate(e_close([nfa.start_State]), token_list)
    seen = {start.nfa_states: start}
    queue = [start]

    while queue:
        curr = queue.pop(0)
        symbols = {sym for s in curr.nfa_states for sym in s.transitions if sym != 'Ɛ'}
        for sym in symbols:
            next_states = e_close(t for s in curr.nfa_states if sym in s.transitions for t in s.transitions[sym])
            if next_states not in seen:
                seen[next_states] = DFAstate(next_states, token_list)
                queue.append(seen[next_states])
            curr.transitions[sym] = seen[next_states]

    return start


def test_DFA(start: DFAstate, tape: str):
    """Simulates the DFA on an input string to test if the entire string matches a single token.
    
    Args:
        start: The starting DFAstate of the combined DFA.
        tape: The input string to parse.
    Returns:
        The matched token name if the entire string reaches an accepting state, 
        otherwise -1.
    """
    curr = start
    for c in tape:
        if c not in curr.transitions:
            return -1
        curr = curr.transitions[c]
    return curr.token if curr.token is not None else -1