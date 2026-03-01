
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


def simpleNFA(c: chr):
    start_State = State()
    accept_State = State()
    start_State.transitions[f"{c}"] = accept_State
    NFA(start_State, accept_State)
    return NFA


def epsilonNFA_Builder(regex: str):
    postfix_regex = regex_to_postfix(regex)
    buffer = []
    uni_operators = {
        "*": lambda x: kleene_NFA(x),
        "+": lambda x: closure_NFA(x),
        "?": lambda x: optionalNFA(x),
    }
    bi_operators = {
        ".": lambda x, y: concat_NFAs(x, y),
        "|": lambda x, y: union_NFAs(x, y)
    }
    for c in postfix_regex:

        if c.isalnum():
            buffer.append(simpleNFA(c))

        elif c in uni_operators:
            buffer[-1] = uni_operators[c](buffer[-1])

        elif c in bi_operators:
            nfa = bi_operators[c](buffer[-1], buffer[-2])
            buffer.pop()
            buffer.pop()
            buffer.append(nfa)

    return buffer[0]


print(regex_to_postfix("ab|bd|cd"))
