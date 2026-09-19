# Lexical Analyzer Visualizer Wiki

This Wiki explains the design behind the Lexical Analyzer Visualizer. It starts with ordered token specifications, constructs automata using the algorithms studied in CSC339, and scans source text using longest-match tokenization.

The project has two layers:

1. A Python core that implements regex preprocessing, Thompson's construction, subset construction, and scanning.
2. A browser interface that runs the Python core through Pyodide and visualizes its output.

The browser is not a replacement implementation. It is a view over the same automata and scanner used by the Python code.

## Reading guide

- [Theory and Algorithms](Theory-and-Algorithms.md) explains each stage and its cost.
- [Architecture](Architecture.md) maps the formal model to Python, JavaScript, and browser components.
- [User Guide](User-Guide.md) explains every tab and keyboard shortcut.
- [Development](Development.md) covers tests, animation rendering, and maintenance.
- [References](References.md) lists the conceptual sources used by the project.

## Pipeline at a glance

![Regex to NFA to DFA to scanner pipeline](../assets/pipeline.svg)

The important idea is that token priority is part of the recognizer. When a DFA state contains several accepting NFA states, the token that appeared first in the specification list is attached to that DFA state. During scanning, this rule is applied only after the longest accepted prefix has been found.

## Example

Consider these rules in this order:

```text
KW_IF  = if
ID     = [A-Za-z][A-Za-z0-9_]*
ASSIGN = =
EQ     = ==
```

- `if` matches both `KW_IF` and `ID` with length 2, so priority selects `KW_IF`.
- `ifx` is emitted as `ID`, because a length 3 match wins before priority is considered.
- `==` is emitted as `EQ`, because it is longer than the one-character `ASSIGN` match.

This separation between length and priority is central to the scanner's correctness.

## Project status

The browser application includes editable token rules, source scanning, NFA and DFA diagrams, an animated execution trace, dark mode, responsive layouts, local persistence, and keyboard shortcuts. The regression suite covers the main correctness rules of the Python core.

Current limitations and possible extensions are documented in [Theory and Algorithms](Theory-and-Algorithms.md#limitations-and-next-steps).
