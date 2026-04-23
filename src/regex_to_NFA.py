from linecache import cache


# represents the data of one state
class State:
    def __init__(self):
        # our transition table that maps a char to a state
        self.transitions: dict[str, list[State]] = {}

    # adds a transition to multiple or a singular state if not already present
    def add_transition(self, char, target_state):
        if char not in self.transitions:
            self.transitions[char] = []
        self.transitions[char].append(target_state)

class accept_state(State):
    def init(self, token: str):
        super().init({})
        self.token = token


# represents the data of one NFA
class NFA:
    def __init__(self, start_state: State, accept_state: State):
        self.start_State = start_state
        self.accept_State = accept_state


# we need to display the concat operation in the regex to process correctly
def insert_concat_symbol(regex: str):
    new_regex = [""] * len(regex) * 2
    for i in range(len(regex) - 1):
        if regex[i] not in ["|", "("] and regex[i + 1] not in ["|", ")", "*", "+"]:
            new_regex.append(regex[i])
            new_regex.append(".")
        else:
            new_regex.append(regex[i])
    new_regex.append(regex[-1])
    return "".join(new_regex)


# We used the shunting-yard algo here
# very similar to the one we took in csc212
def regex_to_postfix(regex: str):
    operations_precedence = {"*": 3, "+": 3, "?": 3, ".": 2, "|": 1}
    regex = insert_concat_symbol(regex)
    result = []
    operators_stack = []

    for c in regex:

        # operand
        if c.isalnum():
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

    for _ in range(len(operators_stack)):
        result.append(operators_stack.pop())

    return "".join(result)


def concat_NFAs(nfa1: NFA, nfa2: NFA):
    nfa1.accept_State.add_transition('Ɛ', nfa2.start_State)
    new_nfa = NFA(nfa1.start_State, nfa2.accept_State)
    return new_nfa

def concatNFAs(NFA1:NFA, NFA2:NFA):
    #result NFA start state and accept state
    start_State = NFA1.start_State
    accept_State = NFA2.accept_State
    #add epsilon transition from NFA1 accept state to NFA2 start state
    NFA1.accept_State.__class__ = State
    del NFA1.accept_State.token
    NFA1.accept_State.transitions["ε"] = NFA2.start_State


def kleene_NFA(nfa: NFA):
    # START state to the END state on epsilon
    nfa.start_State.add_transition('Ɛ', nfa.accept_State)
    # END state to the START state on epsilon
    nfa.accept_State.add_transition('Ɛ',nfa.start_State)
    new_nfa = NFA(nfa.start_State, nfa.accept_State)
    return new_nfa


def closure_NFA(nfa: NFA):
    # END state to the START state on epsilon
    nfa.accept_State.add_transition('Ɛ', nfa.start_State)
    new_nfa = NFA(nfa.start_State, nfa.accept_State)
    return new_nfa


def union_NFAs(nfa1: NFA, nfa2: NFA):

    new_start_State = State()

    # point to both start states of the two NFAs
    new_start_State.add_transition('Ɛ', [nfa1.start_State, nfa2.start_State])

    new_accept_State = State()

    # combine the accept states of the two NFAs
    nfa1.accept_State.add_transition('Ɛ', new_start_State)
    nfa2.accept_State.add_transition('Ɛ', new_accept_State)

    new_nfa = NFA(new_start_State, new_accept_State)
    return new_nfa


def optionalNFA(nfa: NFA):
    new_accepted_state = State()
    nfa.start_State.add_transition('Ɛ', new_accepted_state)
    nfa.accept_State.add_transition('Ɛ', new_accepted_state)
    new_nfa = (nfa.start_State, new_accepted_state)
    return new_nfa


def simpleNFA(c: chr, token: str):
    start_State = State({})
    accept_State = accept_state(token)
    start_State.add_transition(c, accept_State)
    return NFA(start_State, accept_State)


def epsilonNFA_Builder(regex: str,token: str):
    postfix_regex = regex_to_postfix(regex)
    buffer = []
    unioperators = {
        "*": lambda x: kleene_NFA(x),
        "+": lambda x: closure_NFA(x),
        "?": lambda x: optionalNFA(x),
    }
    bioperators = {
        ".": lambda x, y: concatNFAs(x, y),
        "|": lambda x, y: union_NFAs(x, y)
    }
    for c in postfix_regex:

        if c.isalnum():
            buffer.append(simpleNFA(c,token))

        elif c in unioperators.keys():
            buffer[-1] = unioperators[c](buffer[-1])

        elif c in bioperators.keys():
            nfa = bioperators[c](buffer[-2],buffer[-1])
            buffer.pop()
            buffer.pop()
            buffer.append(nfa)

    return buffer[0]


def epsilonClosure(state: State) -> set[State]:
    closure = set()
    deque: list[State] = state.transitions['Ɛ']

    while deque:
        item = deque.pop()
        closure.add(item)
        for value in item.transitions['Ɛ']:
            if value not in closure:
                deque.append(value)

    return closure

def test_NFA(current_state: State, input_tape:str, current_index: int):
    current_closure = epsilonClosure(current_state)
    possible_transitions = current_state.transitions[input_tape[current_index]]

    if type(current_state) is accept_state:
        return current_state.token

    if not current_closure and not possible_transitions:
        return False

    for state in current_closure:
        test_NFA(state, input_tape, current_index)

    for state in possible_transitions:
        test_NFA(state, input_tape, current_index + 1)





nfa = epsilonNFA_Builder("ab","True")
print(test_NFA(nfa,"ab"))


print(regex_to_postfix("ab|bd|cd"))
