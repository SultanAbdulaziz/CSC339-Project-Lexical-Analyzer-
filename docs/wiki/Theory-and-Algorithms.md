# Theory and Algorithms

## 1. Formal model

Both automata follow the standard five-tuple model:

```text
(Q, Sigma, delta, q0, F)
```

- `Q` is the set of states.
- `Sigma` is the input alphabet.
- `delta` is the transition function.
- `q0` is the initial state.
- `F` is the set of accepting states.

For an NFA, `delta` returns a set of possible states and may also follow epsilon transitions. For a DFA, `delta` returns one target state for each state and input character.

Accepting states carry a token name. This connects the language recognized by the automaton to the token emitted by the scanner.

## 2. Regex preprocessing

The project parses the supported regex language without using Python's `re` module.

### Character class expansion

The supported classes are expanded into explicit unions. For example:

```text
[0-9]  -> (0|1|2|3|4|5|6|7|8|9)
```

This keeps the later stages simple because Thompson's construction only needs literals and the core operators.

### Explicit concatenation

Concatenation is implicit in the input syntax, so the parser inserts a dot as an internal operator:

```text
ab(c|d)*  -> a.b.(c|d)*
```

Escaped metacharacters such as `\+` are kept as one literal operand.

### Infix to postfix

The shunting-yard algorithm converts the expression to postfix form using this precedence:

| Operators | Precedence |
| --- | ---: |
| `*`, `+`, `?` | 3 |
| explicit concatenation `.` | 2 |
| union `|` | 1 |

Postfix form allows the NFA builder to evaluate the regex with a stack.

## 3. Thompson's construction

Each literal starts as a two-state NFA. Operators combine smaller fragments using fixed local rules.

![Thompson construction animation](../assets/thompson-construction.gif)

| Operation | Construction idea |
| --- | --- |
| Concatenation `AB` | Connect the accept state of `A` to the start of `B` with epsilon. |
| Union `A|B` | Add a new start and accept state, then branch and merge with epsilon transitions. |
| Kleene star `A*` | Add paths for zero occurrences, one occurrence, and repetition. |
| Positive closure `A+` | Loop from the accept state to the start without adding the zero-occurrence path. |
| Optional `A?` | Add an epsilon path that skips `A`. |

The postfix evaluator pushes simple NFAs for operands. A unary operator replaces the top fragment, while a binary operator pops two fragments and pushes their combination.

### Combining token NFAs

After one NFA is built for every token, a new global start state is added. It has an epsilon transition to the start of each token NFA. The result recognizes the union of all token languages while preserving their distinct accepting labels.

## 4. Subset construction

A DFA state represents a frozen set of NFA states. The initial DFA state is the epsilon-closure of the combined NFA start state.

![Subset construction animation](../assets/subset-construction.gif)

For every unprocessed DFA state and alphabet symbol:

1. Follow that symbol from every NFA state in the set.
2. Take the epsilon-closure of all reached states.
3. Reuse the resulting set if it has already been seen, or create a new DFA state.
4. Add the deterministic transition.

An empty closure maps to one shared trap state. If a closure contains NFA accept states, its DFA state becomes accepting.

### Resolving accepting-state conflicts

A single DFA state may contain accepting states from multiple token NFAs. The implementation checks token names in specification order and stores the first one found. This resolves equal-length ambiguity before scanning begins.

## 5. Maximal-munch scanning

The scanner begins at the current source position and walks through the DFA. It does not stop at the first accepting state. Instead, it remembers the most recent accepting state and continues until the next transition reaches the trap state.

![Maximal-munch animation](../assets/maximal-munch.gif)

At that point:

- If an accepting state was recorded, the scanner emits the text ending at that position.
- If no accepting state was recorded, the current character starts no valid token and scanning stops with a lexical error.
- After a token is emitted, scanning restarts from the first character after that lexeme.

For `==`, the scanner first reaches an accepting `ASSIGN` state after the first `=`. It keeps going, reaches an accepting `EQ` state after the second `=`, and records the longer match. When the following character fails, `EQ` is emitted.

## 6. Cost analysis

Let:

- `k` be the number of token specifications.
- `R` be the total expanded regex length.
- `|Q|` be the number of NFA states.
- `|Sigma|` be the alphabet size.
- `|Q_DFA|` be the number of reachable DFA states.
- `|w|` be the source length.

| Stage | Time | Space |
| --- | --- | --- |
| Regex preprocessing | `O(R)` | `O(R)` |
| Thompson construction | `O(R)` | `O(R)` |
| Subset construction | `O(2^|Q| * |Sigma| * |Q|)` worst case | `O(|Q_DFA| * (|Q| + |Sigma|))` |
| Scanning | `O(|w|^2)` worst case, close to `O(|w|)` for the provided token set | `O(T)`, where `T` is the number of emitted tokens |

Subset construction is the theoretical bottleneck because a DFA can contain one state for every subset of NFA states. Most of those subsets are unreachable for ordinary token definitions, so practical builds are much smaller than the worst-case bound.

The scanner can rescan lookahead characters after returning to the last accepting position. This explains its quadratic theoretical bound. A production implementation could use a different buffering strategy when strict linear time is required.

## 7. Limitations and next steps

The current implementation is intentionally small enough to study. Its main limitations are:

- Only predefined character classes are expanded.
- DFA minimization is not implemented.
- The scanner stops at the first lexical error.
- Whitespace is skipped by scanner logic rather than represented as token rules.
- Graph views cap the number of displayed states to protect browser responsiveness.

Reasonable next steps include a general character-class parser, DFA minimization, error recovery, import and export of token specifications, and additional property-based tests.
