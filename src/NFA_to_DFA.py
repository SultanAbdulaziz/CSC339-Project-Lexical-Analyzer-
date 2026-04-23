from regex_to_NFA22 import NFA, accept_state, epsilonClosure,epsilonNFA_Builder
from Main import *


class DFAstate:
    def __init__(self, nfa_states):
        self.nfa_states = frozenset(nfa_states)
        self.transitions: dict[str, 'DFAstate'] = {}
        self.token = next((s.token for s in nfa_states if isinstance(s, accept_state)), None)


def e_close(states):
    states = list(states)
    result = set(states)
    for s in states:
        result |= epsilonClosure(s)
    return frozenset(result)


def NFA_to_DFA(nfa: NFA):
    start = DFAstate(e_close([nfa.start_State]))
    seen = {start.nfa_states: start}
    queue = [start]

    while queue:
        curr = queue.pop(0)
        symbols = {sym for s in curr.nfa_states for sym in s.transitions if sym != 'Ɛ'}
        for sym in symbols:
            next_states = e_close(t for s in curr.nfa_states if sym in s.transitions for t in s.transitions[sym])
            if next_states not in seen:
                seen[next_states] = DFAstate(next_states)
                queue.append(seen[next_states])
            curr.transitions[sym] = seen[next_states]

    return start


def test_DFA(start: DFAstate, tape: str):
    curr = start
    for c in tape:
        if c not in curr.transitions:
            return -1
        curr = curr.transitions[c]
    return curr.token if curr.token is not None else -1

def change(regex: str) -> str:
    for key, val in bracket_map.items():
        regex = regex.replace(f"[{key}]", val)
    return regex

h = "[A-Za-z][A-Za-z0-9_]*"

nfa = epsilonNFA_Builder(change(h),"IF_KW")

print(test_DFA(NFA_to_DFA(nfa),"HelloWorld"))