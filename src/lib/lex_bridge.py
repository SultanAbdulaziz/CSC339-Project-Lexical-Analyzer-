"""
Bridge module exposed to the JS frontend via Pyodide.

Everything the frontend needs is here:
  - build(token_specs_json) -> summary_json  (build NFAs + DFA from token specs)
  - scan_text(source) -> tokens_json         (full scan, all tokens)
  - dfa_dot(opts) -> dot string              (DOT for the DFA graph)
  - nfa_dot(token_name, opts) -> dot string  (DOT for a token's NFA, or combined)

  Step-by-step API:
  - step_init(source) -> state_json
  - step_advance() -> state_json
  - step_run_to_end() -> state_json
  - step_run_to_next_token() -> state_json
  - step_reset() -> state_json

The user's source files (regex_to_NFA.py, NFA_to_DFA.py) are imported
unchanged. This module wraps them with a JSON-friendly surface so the
JS side never sees raw Python objects.
"""
import json
import html as html_lib

from regex_to_NFA import (
    NFA,
    State,
    accept_State,
    NFA_Builder,
    combine_NFAs,
)
from NFA_to_DFA import (
    DFA,
    DFA_State,
    DFA_Accept_State,
    DFA_Trap_State,
    NFA_to_DFA,
    expand_regex,
)


EPSILON_CHAR = "Ɛ"  # the project's epsilon glyph


# ---------------------------------------------------------------------------
# Module-level state. The frontend holds the build "session"; we keep handles
# here so step-by-step calls don't have to round-trip Python objects to JS.
# ---------------------------------------------------------------------------

_state: dict = {
    "dfa": None,
    "token_nfas": {},    # token name -> NFA
    "combined_nfa": None,
    "token_order": [],   # priority order from the spec
}

_stepper: dict | None = None


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(token_specs_json: str) -> str:
    """Build NFAs + DFA from a JSON list of {name, regex} pairs.

    Returns a JSON summary: { ok, error, dfa_states, accept_states,
                              alphabet_size, build_ms, token_count }.
    """
    import time
    try:
        specs = json.loads(token_specs_json)
        token_dict: dict[str, str] = {}
        for entry in specs:
            name = (entry.get("name") or "").strip()
            regex = entry.get("regex") or ""
            if name and regex:
                token_dict[name] = regex

        if not token_dict:
            return json.dumps({"ok": False, "error": "No valid token specs."})

        t0 = time.perf_counter()
        # Individual NFAs (for the NFA tab — we want fresh copies the
        # combined/DFA builds won't mutate, since combine_NFAs / subset
        # construction can mutate accept_State sets).
        token_nfas = {
            n: NFA_Builder(expand_regex(r), n) for n, r in token_dict.items()
        }
        token_nfas_for_combine = [
            NFA_Builder(expand_regex(r), n) for n, r in token_dict.items()
        ]
        combined = combine_NFAs(token_nfas_for_combine)
        token_nfas_for_dfa = [
            NFA_Builder(expand_regex(r), n) for n, r in token_dict.items()
        ]
        combined_for_dfa = combine_NFAs(token_nfas_for_dfa)
        dfa = NFA_to_DFA(combined_for_dfa, list(token_dict.keys()))
        build_ms = (time.perf_counter() - t0) * 1000

        _state["dfa"] = dfa
        _state["token_nfas"] = token_nfas
        _state["combined_nfa"] = combined
        _state["token_order"] = list(token_dict.keys())

        return json.dumps({
            "ok": True,
            "error": None,
            "dfa_states": len(dfa.Q),
            "accept_states": len(dfa.accept_States),
            "alphabet_size": len(dfa.alphabet),
            "token_count": len(token_dict),
            "build_ms": round(build_ms, 1),
        })
    except Exception as e:  # noqa: BLE001
        return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

def scan_text(source: str) -> str:
    """Run a full maximal-munch scan. Returns JSON with tokens + error."""
    if _state["dfa"] is None:
        return json.dumps({"ok": False, "error": "DFA not built yet."})

    stepper = _Stepper(_state["dfa"], source)
    stepper.run_to_end()
    return json.dumps({
        "ok": stepper.error_message is None,
        "error": stepper.error_message,
        "tokens": [
            {"lexeme": l, "token": t, "line": ln, "col": c}
            for (l, t, ln, c) in stepper.tokens
        ],
    })


# ---------------------------------------------------------------------------
# Graph DOT generation
# ---------------------------------------------------------------------------

def _collect_nfa_states(initial: State) -> dict[int, State]:
    visited: dict[int, State] = {}
    queue: list[State] = [initial]
    while queue:
        s = queue.pop(0)
        if id(s) in visited:
            continue
        visited[id(s)] = s
        for _, targets in s.transitions.items():
            for t in targets:
                if id(t) not in visited:
                    queue.append(t)
    return visited


def _collect_dfa_states(initial: DFA_State) -> dict[int, DFA_State]:
    visited: dict[int, DFA_State] = {}
    queue: list[DFA_State] = [initial]
    while queue:
        s = queue.pop(0)
        if id(s) in visited:
            continue
        visited[id(s)] = s
        for _, target in s.transitions.items():
            if id(target) not in visited:
                queue.append(target)
    return visited


def _escape_dot_label(c: str) -> str:
    if c == EPSILON_CHAR:
        return "ε"
    return c.replace("\\", "\\\\").replace("\"", "\\\"")


def nfa_dot(token_name: str | None = None, max_states: int = 80) -> str:
    """DOT graph for a token's NFA, or the combined NFA if token_name is None."""
    if _state["dfa"] is None:
        return "digraph G { label=\"Build the DFA first.\" }"

    if token_name is None or token_name == "__combined__":
        nfa = _state["combined_nfa"]
    else:
        nfa = _state["token_nfas"].get(token_name)
        if nfa is None:
            return f"digraph G {{ label=\"Unknown token: {token_name}\" }}"

    all_states = _collect_nfa_states(nfa.initial_State)
    total = len(all_states)
    truncated = total > max_states
    if truncated:
        states: dict[int, State] = {}
        queue: list[State] = [nfa.initial_State]
        seen: set[int] = set()
        while queue and len(states) < max_states:
            s = queue.pop(0)
            if id(s) in seen:
                continue
            seen.add(id(s))
            states[id(s)] = s
            for _, targets in s.transitions.items():
                for t in targets:
                    if id(t) not in seen:
                        queue.append(t)
    else:
        states = all_states

    # Assign short sequential labels in BFS order so nodes are q0, q1, ...
    short: dict[int, str] = {}
    bfs: list[State] = [nfa.initial_State]
    bfs_seen: set[int] = set()
    n = 0
    while bfs:
        s = bfs.pop(0)
        if id(s) in bfs_seen or id(s) not in states:
            continue
        bfs_seen.add(id(s))
        short[id(s)] = f"q{n}"
        n += 1
        for _, targets in s.transitions.items():
            for t in targets:
                if id(t) not in bfs_seen:
                    bfs.append(t)

    lines = [
        "digraph NFA {",
        "  rankdir=LR;",
        "  bgcolor=\"transparent\";",
        "  graph [pad=\"0.3\", ranksep=\"0.6\", nodesep=\"0.35\"];",
        "  node [shape=circle, style=filled, fillcolor=\"#fafaf9\", color=\"#78716c\","
        " fontname=\"Helvetica Neue, Arial, sans-serif\", fontsize=9,"
        " width=0.38, penwidth=1.2];",
        "  edge [fontname=\"Helvetica Neue, Arial, sans-serif\", fontsize=8,"
        " color=\"#a8a29e\", arrowsize=0.7, penwidth=1.0];",
        "  __start [shape=point, width=0.12, color=\"#b45309\"];",
        f"  __start -> n{id(nfa.initial_State)} [color=\"#b45309\", penwidth=1.5];",
    ]

    for sid, s in states.items():
        lbl = short.get(sid, "")
        if isinstance(s, accept_State):
            lines.append(
                f"  n{sid} [shape=doublecircle, label=\"{lbl}\\n{s.token}\","
                " fillcolor=\"#f0fdf4\", color=\"#16a34a\","
                " fontcolor=\"#166534\", fontsize=8, penwidth=1.5];"
            )
        else:
            lines.append(f"  n{sid} [label=\"{lbl}\", fontcolor=\"#57534e\"];")

    edge_chars: dict[tuple[int, int], list[str]] = {}
    for sid, s in states.items():
        for char, targets in s.transitions.items():
            for t in targets:
                if id(t) in states:
                    edge_chars.setdefault((sid, id(t)), []).append(char)

    for (src, dst), chars in edge_chars.items():
        chars_sorted = sorted(chars, key=lambda c: (c != EPSILON_CHAR, c))
        if len(chars_sorted) > 8:
            label = f"{_escape_dot_label(chars_sorted[0])} ... +{len(chars_sorted)-1}"
        else:
            label = ", ".join(_escape_dot_label(c) for c in chars_sorted)
        is_eps = all(c == EPSILON_CHAR for c in chars_sorted)
        if is_eps:
            lines.append(
                f"  n{src} -> n{dst} [label=\"\u03b5\", style=dashed,"
                " color=\"#d6d3d1\", fontcolor=\"#a8a29e\"];"
            )
        else:
            lines.append(
                f"  n{src} -> n{dst} [label=\"{label}\","
                " color=\"#44403c\", fontcolor=\"#44403c\"];"
            )

    if truncated:
        lines.append(
            f"  __legend [shape=note, style=filled, fillcolor=\"#fef3c7\","
            f" color=\"#b45309\", fontcolor=\"#92400e\", fontsize=8,"
            f" label=\"Showing first {max_states} of {total} states (BFS)\"];"
        )
    lines.append("}")
    return "\n".join(lines)


def dfa_dot(
    max_states: int = 100,
    hide_trap: bool = True,
    highlight_state_id: int | None = None,
) -> str:
    """DOT graph for the DFA, optionally with a state highlighted."""
    if _state["dfa"] is None:
        return "digraph G { label=\"Build the DFA first.\" }"

    dfa = _state["dfa"]
    all_states = _collect_dfa_states(dfa.initial_State)
    if hide_trap:
        all_states = {
            sid: s for sid, s in all_states.items()
            if not isinstance(s, DFA_Trap_State)
        }
    total = len(all_states)
    truncated = total > max_states

    if truncated:
        states: dict[int, DFA_State] = {}
        queue: list[DFA_State] = [dfa.initial_State]
        seen: set[int] = set()
        while queue and len(states) < max_states:
            s = queue.pop(0)
            if id(s) in seen:
                continue
            if hide_trap and isinstance(s, DFA_Trap_State):
                continue
            seen.add(id(s))
            states[id(s)] = s
            for _, target in s.transitions.items():
                if id(target) not in seen:
                    queue.append(target)
    else:
        states = all_states

    # Short BFS-ordered labels
    short_label: dict[int, str] = {}
    queue2: list[DFA_State] = [dfa.initial_State]
    seen2: set[int] = set()
    order = 0
    while queue2:
        s = queue2.pop(0)
        if id(s) in seen2 or id(s) not in states:
            continue
        seen2.add(id(s))
        short_label[id(s)] = f"S{order}"
        order += 1
        for _, target in s.transitions.items():
            if id(target) not in seen2:
                queue2.append(target)

    lines = [
        "digraph DFA {",
        "  rankdir=LR;",
        "  bgcolor=\"transparent\";",
        "  graph [pad=\"0.3\", ranksep=\"0.7\", nodesep=\"0.4\"];",
        "  node [shape=circle, style=filled, fillcolor=\"#fafaf9\", color=\"#78716c\","
        " fontname=\"Helvetica Neue, Arial, sans-serif\", fontsize=9,"
        " width=0.45, penwidth=1.2];",
        "  edge [fontname=\"Helvetica Neue, Arial, sans-serif\", fontsize=7,"
        " color=\"#a8a29e\", arrowsize=0.65, penwidth=1.0];",
        "  __start [shape=point, width=0.12, color=\"#b45309\"];",
        f"  __start -> n{id(dfa.initial_State)} [color=\"#b45309\", penwidth=1.5];",
    ]

    for sid, s in states.items():
        lbl = short_label.get(sid, "?")
        is_highlighted = (highlight_state_id is not None and sid == highlight_state_id)

        if isinstance(s, DFA_Accept_State):
            fill  = "#fef3c7" if is_highlighted else "#f0fdf4"
            color = "#b45309" if is_highlighted else "#16a34a"
            fontc = "#92400e" if is_highlighted else "#166534"
            pw    = "2.5"     if is_highlighted else "1.5"
            lines.append(
                f"  n{sid} [shape=doublecircle, label=\"{lbl}\\n{s.token}\","
                f" fillcolor=\"{fill}\", color=\"{color}\","
                f" fontcolor=\"{fontc}\", fontsize=8, penwidth={pw}];"
            )
        else:
            fill  = "#fef3c7" if is_highlighted else "#fafaf9"
            color = "#b45309" if is_highlighted else "#78716c"
            fontc = "#92400e" if is_highlighted else "#57534e"
            pw    = "2.5"     if is_highlighted else "1.2"
            lines.append(
                f"  n{sid} [label=\"{lbl}\", fillcolor=\"{fill}\","
                f" color=\"{color}\", fontcolor=\"{fontc}\", penwidth={pw}];"
            )

    edge_chars: dict[tuple[int, int], list[str]] = {}
    for sid, s in states.items():
        for char, target in s.transitions.items():
            if id(target) in states:
                edge_chars.setdefault((sid, id(target)), []).append(char)

    for (src, dst), chars in edge_chars.items():
        chars_sorted = sorted(chars)
        if len(chars_sorted) > 8:
            label = f"{_escape_dot_label(chars_sorted[0])} ... +{len(chars_sorted)-1}"
        else:
            label = ", ".join(_escape_dot_label(c) for c in chars_sorted)
        # Highlight edges leaving the current state
        if highlight_state_id is not None and src == highlight_state_id:
            lines.append(
                f"  n{src} -> n{dst} [label=\"{label}\","
                " color=\"#b45309\", fontcolor=\"#92400e\", penwidth=1.5];"
            )
        else:
            lines.append(f"  n{src} -> n{dst} [label=\"{label}\"];")

    if truncated:
        lines.append(
            f"  __legend [shape=note, style=filled, fillcolor=\"#fef3c7\","
            f" color=\"#b45309\", fontcolor=\"#92400e\", fontsize=8,"
            f" label=\"Showing first {max_states} of {total} states (BFS)\"];"
        )
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Step-by-step scanner
# ---------------------------------------------------------------------------

class _Stepper:
    def __init__(self, dfa, source):
        self.dfa = dfa
        self.source = source
        self.pos = 0
        self.inner_i = 0
        self.line = 1
        self.col = 1
        self.tokens = []
        
        self.current_state = dfa.initial_State
        self.last_accept_state = None
        self.last_accept_pos = None
        self.last_accept_token = None
        
        self.error_message = None
        self.last_event = "Scanner initialized."
        self.step_count = 0
        
        self._skip_whitespace()

    def _skip_whitespace(self):
        # Safely skip spaces, tabs, and newlines before processing tokens
        while self.pos < len(self.source) and self.source[self.pos] in [' ', '\t', '\n', '\r']:
            char = self.source[self.pos]
            if char == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.pos += 1
            
    def state_json(self):
        return json.dumps({
            "pos": self.pos,
            "line": self.line,
            "col": self.col,
            "inner_i": self.inner_i,
            "last_accept_pos": self.last_accept_pos,
            "last_accept_token": self.last_accept_token,
            "current_state_id": id(self.current_state) if self.current_state else None,
            "tokens": [{"lexeme": l, "token": t, "line": ln, "col": c} for l, t, ln, c in self.tokens],
            "last_event": self.last_event,
            "error": self.error_message,
            "step_count": self.step_count,
            "source_len": len(self.source)
        })

    def step(self):
        if self.error_message or self.pos >= len(self.source):
            self.last_event = "Completed."
            return
            
        self.step_count += 1
        cursor = self.pos + self.inner_i
        
        # If we reached the end of the file while scanning a token
        if cursor >= len(self.source):
            self._handle_trap_or_eof(eof=True)
            return
            
        char = self.source[cursor]
        next_state = self.dfa.δ(self.current_state, char)
        
        if isinstance(next_state, DFA_Trap_State):
            # We hit the trap state. Fallback to maximal munch!
            self.current_state = next_state
            self._handle_trap_or_eof(eof=False)
        else:
            # Valid move forward
            self.current_state = next_state
            if isinstance(next_state, DFA_Accept_State):
                self.last_accept_state = next_state
                self.last_accept_pos = cursor
                self.last_accept_token = next_state.token
                self.last_event = f"Read '{char}' -> Accept ({self.last_accept_token})"
            else:
                self.last_event = f"Read '{char}' -> Moving state"
            self.inner_i += 1

    def _handle_trap_or_eof(self, eof):
        if self.last_accept_state is not None:
            # SUCCESS: We found a valid token prefix previously!
            lexeme = self.source[self.pos : self.last_accept_pos + 1]
            self.tokens.append((lexeme, self.last_accept_token, self.line, self.col))
            
            # Update line/col
            for c in lexeme:
                if c == '\n':
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
                    
            reason = "EOF" if eof else "Trap state"
            self.last_event = f"{reason}. Emitted '{self.last_accept_token}'."
            
            # Reset for next token
            self.pos = self.last_accept_pos + 1
            self.inner_i = 0
            self.current_state = self.dfa.initial_State
            self.last_accept_state = None
            self.last_accept_pos = None
            self.last_accept_token = None
            self._skip_whitespace()
        else:
            # ERROR FIX: No valid token found before hitting Trap. Stop gracefully.
            if eof:
                self.error_message = "Unexpected end of file."
            else:
                char = self.source[self.pos + self.inner_i]
                self.error_message = f"Invalid character '{char}' at line {self.line}, col {self.col}"
            self.last_event = f"Error: {self.error_message}"

    def run_to_end(self):
        limit = 50000
        while self.pos < len(self.source) and not self.error_message and limit > 0:
            self.step()
            limit -= 1

    def run_to_next_token(self):
        start_tokens = len(self.tokens)
        limit = 5000
        while self.pos < len(self.source) and not self.error_message and len(self.tokens) == start_tokens and limit > 0:
            self.step()
            limit -= 1

def step_init(source: str) -> str:
    global _stepper
    if _state["dfa"] is None:
        return json.dumps({"ok": False, "error": "DFA not built yet."})
    _stepper = _Stepper(_state["dfa"], source)
    return _stepper.state_json()


def step_advance() -> str:
    if _stepper is None:
        return json.dumps({"error": "Stepper not initialized."})
    _stepper.step()
    return _stepper.state_json()


def step_run_to_end() -> str:
    if _stepper is None:
        return json.dumps({"error": "Stepper not initialized."})
    _stepper.run_to_end()
    return _stepper.state_json()


def step_run_to_next_token() -> str:
    if _stepper is None:
        return json.dumps({"error": "Stepper not initialized."})
    _stepper.run_to_next_token()
    return _stepper.state_json()


def step_reset(source: str) -> str:
    return step_init(source)

def step_trace_dot(source: str) -> str:
    if _state["dfa"] is None:
        return ""
        
    try:
        temp_stepper = _Stepper(_state["dfa"], source)
        nodes = []
        edges = []

        def get_node_attrs(st):
            if st is None:
                return "Trap", "#fee2e2", "#ef4444", "circle"
            elif isinstance(st, DFA_Trap_State):
                return "Trap", "#fee2e2", "#ef4444", "circle"
            elif isinstance(st, DFA_Accept_State):
                return f"Accept\\n({st.token})", "#dcfce7", "#22c55e", "doublecircle"
            elif st == _state["dfa"].initial_State:
                return "Start", "#f5f5f4", "#78716c", "circle"
            else:
                return f"S{id(st) % 1000}", "#f5f5f4", "#78716c", "circle"

        step_idx = 0
        lbl, bg, fg, shape = get_node_attrs(temp_stepper.current_state)
        nodes.append(f'  step_{step_idx} [label="{lbl}", shape="{shape}", fillcolor="{bg}", color="{fg}"];')

        # Limit graph length to prevent WebAssembly memory crashes
        MAX_STEPS = 120 

        while step_idx < MAX_STEPS:
            # Check if we finished successfully or hit an error
            if temp_stepper.last_event.startswith("Completed") or temp_stepper.error_message:
                break

            cursor = temp_stepper.pos + temp_stepper.inner_i
            char = source[cursor] if cursor < len(source) else "EOF"
            
            # Safely escape characters for Graphviz DOT
            char_lbl = char.replace('\\', '\\\\').replace('"', '\\"').replace('{', '\\{').replace('}', '\\}')
            if char == " ": char_lbl = "SP"
            elif char == "\n": char_lbl = "\\\\n"
            elif char == "\t": char_lbl = "\\\\t"

            temp_stepper.step()
            step_idx += 1

            lbl, bg, fg, shape = get_node_attrs(temp_stepper.current_state)
            nodes.append(f'  step_{step_idx} [label="{lbl}", shape="{shape}", fillcolor="{bg}", color="{fg}"];')
            edges.append(f'  step_{step_idx-1} -> step_{step_idx} [label=" {char_lbl} "];')

        # If the text was really long, add a truncation warning node
        if step_idx >= MAX_STEPS:
            nodes.append(f'  step_limit [label="Graph Truncated\\n(Input too long)", shape="rect", fillcolor="#fef08a", color="#ca8a04"];')
            edges.append(f'  step_{step_idx} -> step_limit [style="dashed"];')

        dot = [
            "digraph Trace {",
            "  rankdir=LR;",
            "  node [fontname=\"monospace\", fontsize=10, style=filled];",
            "  edge [fontname=\"monospace\", fontsize=10];"
        ]
        dot.extend(nodes)
        dot.extend(edges)
        dot.append("}")
        return "\n".join(dot)

    except Exception as e:
        # If Python crashes, draw a red box with the exact error!
        err_msg = str(e).replace('"', '\\"')
        return f'digraph Trace {{ node [shape=rect, fillcolor="#fee2e2", color="#ef4444", style=filled]; Error [label="Python Error:\\n{err_msg}"]; }}'