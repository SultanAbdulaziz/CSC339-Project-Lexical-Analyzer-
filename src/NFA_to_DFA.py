from numpy.f2py.auxfuncs import throw_error


class DState:
    def __init__(self):
        self.transitions: dict[str, DState] = {}
        self.is_accept = False

    def make_accept(self):
        self.is_accept = True

    def add_transition(self, char, target_state):
        if char not in self.transitions:
            self.transitions[char] = target_state
        else:
            throw_error("Transition already exists, fix your coding mistakes please")

