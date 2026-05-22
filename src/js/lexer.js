/**
 * Lexer — Pyodide wrapper.
 *
 * Loads the user's Python lexer code into Pyodide and exposes a clean
 * Promise-based API to the rest of the frontend. The Python source files
 * (regex_to_NFA.py, NFA_to_DFA.py) are loaded unmodified; only lex_bridge.py
 * provides the JSON-friendly surface.
 */

const PYODIDE_PYTHON_FILES = [
  'lib/regex_to_NFA.py',
  'lib/NFA_to_DFA.py',
  'lib/lex_bridge.py',
];

export class Lexer {
  constructor(pyodide) {
    this.pyodide = pyodide;
    // Cache references to Python functions for speed
    this._build = pyodide.globals.get('build');
    this._scan = pyodide.globals.get('scan_text');
    this._nfaDot = pyodide.globals.get('nfa_dot');
    this._dfaDot = pyodide.globals.get('dfa_dot');
    this._stepInit = pyodide.globals.get('step_init');
    this._stepAdvance = pyodide.globals.get('step_advance');
    this._stepRunToEnd = pyodide.globals.get('step_run_to_end');
    this._stepRunToNextToken = pyodide.globals.get('step_run_to_next_token');
    this._stepTraceDot = pyodide.globals.get('step_trace_dot');
  }

  /**
   * Factory: load Pyodide, fetch Python files, import the bridge.
   * @param {(msg: string, percent: number) => void} onProgress
   */
  static async create(onProgress = () => {}) {
    if (typeof loadPyodide !== 'function') {
      throw new Error('Pyodide script did not load. Check your network.');
    }

    onProgress('Initializing Python runtime…', 25);
    const pyodide = await loadPyodide({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.29.4/full/',
    });

    onProgress('Fetching lexer source files…', 55);
    const files = await Promise.all(
      PYODIDE_PYTHON_FILES.map(async (path) => {
        const resp = await fetch(path);
        if (!resp.ok) {
          throw new Error(`Failed to fetch ${path}: HTTP ${resp.status}`);
        }
        const text = await resp.text();
        const name = path.split('/').pop();
        return { name, text };
      })
    );

    onProgress('Loading lexer into Python…', 80);
    for (const { name, text } of files) {
      pyodide.FS.writeFile(name, text, { encoding: 'utf8' });
    }
    pyodide.runPython(`
import sys
if '.' not in sys.path:
    sys.path.insert(0, '.')
from lex_bridge import (
    build, scan_text, nfa_dot, dfa_dot,
    step_init, step_advance, step_run_to_end,
    step_run_to_next_token, step_reset,
    step_trace_dot
)
`);

    onProgress('Ready.', 100);
    return new Lexer(pyodide);
  }

  /**
   * Build NFAs + DFA from token specs.
   * @param {{name: string, regex: string}[]} specs
   * @returns {Promise<object>} summary {ok, error, dfa_states, ...}
   */
  async build(specs) {
    const json = JSON.stringify(specs);
    const result = this._build(json);
    return JSON.parse(result);
  }

  /**
   * Scan a source string. Returns {ok, error, tokens}.
   */
  async scan(source) {
    return JSON.parse(this._scan(source));
  }

  /**
   * DOT source for an NFA. Pass null/undefined for combined NFA.
   */
  async nfaDot(tokenName, maxStates = 80) {
    return this._nfaDot(tokenName ?? '__combined__', maxStates);
  }

  /**
   * DOT source for the DFA. Optionally highlight one state by its Python id().
   */
  async dfaDot({ maxStates = 100, hideTrap = true, highlightStateId = null } = {}) {
    return this._dfaDot(maxStates, hideTrap, highlightStateId);
  }

  // ===== Stepper =====

  async stepInit(source) {
    return JSON.parse(this._stepInit(source));
  }

  async stepAdvance() {
    return JSON.parse(this._stepAdvance());
  }

  async stepRunToEnd() {
    return JSON.parse(this._stepRunToEnd());
  }

  async stepRunToNextToken() {
    return JSON.parse(this._stepRunToNextToken());
  }
  async stepTraceDot(source) {
    return this._stepTraceDot(source);
  }
}
