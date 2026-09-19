# User Guide

## Start the application

From the repository root, run:

```powershell
python -m http.server 8000 --directory src
```

Open [http://localhost:8000](http://localhost:8000). Opening `index.html` directly with a `file://` URL will not work because the browser must fetch the Python modules over HTTP.

The first load downloads Pyodide and the graph libraries. Wait for the status indicator to show the number of DFA states before scanning.

## Tokens tab

Each row contains a token name and regular expression.

- Drag the numbered handle to change priority.
- Use the arrow buttons when dragging is inconvenient or unavailable.
- Add or delete rows as needed.
- Select **Build Automata** after changing the list.
- Select **Reset** to restore the supplied token set.

Priority matters only when matches have equal length. Earlier rows win those ties.

## Scan tab

Enter source text and select **Tokenize**. The result table contains:

- the matched lexeme,
- the selected token name,
- its one-based line number,
- its one-based column number.

The highlighted view uses one stable color per token class. Whitespace remains visible but is not emitted as a token.

If scanning fails, the error identifies the first character that cannot begin a valid token and its position.

## NFA tab

Choose an individual token to inspect its Thompson-constructed NFA, or choose the combined NFA to see the shared start state and all token branches.

Use the state limit when a graph becomes too dense. The graph reports how many states exist and how many are currently displayed.

## DFA tab

This tab shows reachable DFA states produced by subset construction. Double circles are accepting states and include the chosen token name.

The trap state can be hidden because its transitions often dominate the diagram without adding much explanatory value. Hiding it affects only the drawing, not scanning.

## Step-by-Step tab

Enter a short source string and select **Start Debugger**. The graph shows the chronological path through the DFA rather than the whole DFA.

| Control | Behavior |
| --- | --- |
| Play or Pause | Automatically advance the trace. |
| Step | Execute one transition or emission event. |
| Run Token | Continue until the next token is emitted. |
| Run All | Finish immediately. |
| Playback speed | Choose 0.5x, 1x, 2x, or 4x. |
| Stop / Reset | End the active trace and return to the editor. |

The source cursor moves with the scanner. Accepted tokens are colored on the source tape and added to the output table. The event log explains whether each character reached an ordinary state, accepting state, trap state, or end of file.

Short examples are easier to follow. Start with:

```text
int x = 5;
```

## Keyboard shortcuts

| Shortcut | Context | Action |
| --- | --- | --- |
| `Alt + 1` | Anywhere | Tokens tab |
| `Alt + 2` | Anywhere | Scan tab |
| `Alt + 3` | Anywhere | NFA tab |
| `Alt + 4` | Anywhere | DFA tab |
| `Alt + 5` | Anywhere | Step-by-Step tab |
| `Ctrl/Cmd + Enter` | Tokens | Build automata |
| `Ctrl/Cmd + Enter` | Scan | Tokenize source |
| `Ctrl/Cmd + Enter` | Step-by-Step | Start or play |
| `Space` | Initialized step trace | Play or pause |

## Troubleshooting

### The page stays on the loading screen

Confirm that the browser has internet access. Pyodide and the graph libraries are loaded from public CDNs. Open the browser console if the screen reports a network or Content Security Policy error.

### The page says it must be served over HTTP

Run the local server command above and use the `http://localhost:8000` address.

### A build fails

Check for an empty token name, empty regex, unmatched parenthesis, trailing escape, or unsupported character-class syntax.

### The graph is incomplete

The graph view may be capped even though the full automaton was built. Increase the display limit carefully, or inspect an individual token NFA instead of the combined graph.

### Old token rules return after a refresh

The editor intentionally saves rules in local storage. Use **Reset** and confirm the prompt to restore the supplied defaults.
