/**
 * App entry point.
 *
 * Loads Pyodide, initializes the lexer, wires up the UI shell,
 * and mounts each tab.
 */
import { Lexer } from './lexer.js';
import {
  initTheme, initTabs, activateTab, onTabActivated,
  toast, setBuildStatus,
} from './util.js';
import { TokensTab } from './tabs/tokens.js';
import { ScanTab } from './tabs/scan.js';
import { NfaTab } from './tabs/nfa.js';
import { DfaTab } from './tabs/dfa.js';
import { StepTab } from './tabs/step.js';

// ---------------------------------------------------------------------------
// Loading screen helpers
// ---------------------------------------------------------------------------

function setLoadingProgress(message, percent) {
  const status = document.getElementById('loading-status');
  const bar = document.getElementById('loading-bar');
  if (status) status.textContent = message;
  if (bar) bar.style.width = `${percent}%`;
}

function showError(message) {
  document.getElementById('loading-screen').classList.add('hidden');
  document.getElementById('error-screen').classList.remove('hidden');
  document.getElementById('error-message').textContent = message;
}

function showApp() {
  document.getElementById('loading-screen').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
}

// ---------------------------------------------------------------------------
// App state
// ---------------------------------------------------------------------------

const state = {
  lexer: null,
  built: false,
  lastBuildSummary: null,
  tabs: {},
};

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

async function bootstrap() {
  // Detect file:// protocol — Pyodide needs HTTP for module loading + CORS
  if (location.protocol === 'file:') {
    showError(
      'This app must be served over HTTP. ' +
      'Open a terminal in the project folder and run `python -m http.server`, ' +
      'then visit http://localhost:8000/.'
    );
    return;
  }

  // Wait for Pyodide script tag to load
  if (typeof loadPyodide !== 'function') {
    await new Promise((resolve, reject) => {
      let n = 0;
      const id = setInterval(() => {
        if (typeof loadPyodide === 'function') {
          clearInterval(id);
          resolve();
        } else if (++n > 100) { // 10s timeout
          clearInterval(id);
          reject(new Error('Pyodide failed to load (timeout).'));
        }
      }, 100);
    });
  }

  try {
    state.lexer = await Lexer.create(setLoadingProgress);
  } catch (err) {
    showError(`Failed to initialize the lexer: ${err.message}`);
    console.error(err);
    return;
  }

  // Initialize UI shell
  initTheme();
  initTabs();

  // Mount tabs
  state.tabs.tokens = new TokensTab({
    container: document.getElementById('tab-tokens'),
    onBuild: handleBuild,
  });

  state.tabs.scan = new ScanTab({
    container: document.getElementById('tab-scan'),
    getLexer: () => state.lexer,
    isBuilt: state.built,
  });

  state.tabs.nfa = new NfaTab({
    container: document.getElementById('tab-nfa'),
    getLexer: () => state.lexer,
    isBuilt: state.built,
    getTokens: () => state.tabs.tokens.getTokens(),
  });

  state.tabs.dfa = new DfaTab({
    container: document.getElementById('tab-dfa'),
    getLexer: () => state.lexer,
    isBuilt: state.built,
    getStats: () => state.lastBuildSummary,
  });

  state.tabs.step = new StepTab({
    container: document.getElementById('tab-step'),
    getLexer: () => state.lexer,
    isBuilt: state.built,
  });

  // Re-render NFA/DFA when activating their tabs (handles lazy first-render)
  onTabActivated('nfa', () => state.tabs.nfa?.onShow());
  onTabActivated('dfa', () => state.tabs.dfa?.onShow());
  onTabActivated('step', () => state.tabs.step?.onShow());

  initKeyboardShortcuts();

  setBuildStatus('idle', 'Not built');

  // Auto-build on first load with defaults — gives the user something to scan immediately
  showApp();
  await handleBuild(state.tabs.tokens.getTokens(), { silent: true });
}

// ---------------------------------------------------------------------------
// Keyboard shortcuts
// ---------------------------------------------------------------------------

function initKeyboardShortcuts() {
  const tabNames = ['tokens', 'scan', 'nfa', 'dfa', 'step'];

  document.addEventListener('keydown', event => {
    const target = event.target;
    const editing = target instanceof HTMLInputElement ||
      target instanceof HTMLTextAreaElement ||
      target instanceof HTMLSelectElement ||
      target?.isContentEditable;

    const tabIndex = Number(event.key) - 1;
    if (event.altKey && Number.isInteger(tabIndex) && tabNames[tabIndex]) {
      event.preventDefault();
      activateTab(tabNames[tabIndex]);
      return;
    }

    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
      event.preventDefault();
      const active = document.querySelector('.tab-btn[data-active="true"]')?.dataset.tab;
      if (active === 'tokens') document.getElementById('build-btn')?.click();
      if (active === 'scan') document.getElementById('scan-btn')?.click();
      if (active === 'step') {
        const start = document.getElementById('btn-init');
        const play = document.getElementById('btn-play');
        (start && !start.classList.contains('hidden') ? start : play)?.click();
      }
      return;
    }

    if (!editing && event.code === 'Space') {
      const active = document.querySelector('.tab-btn[data-active="true"]')?.dataset.tab;
      if (active === 'step' && !document.getElementById('btn-play')?.disabled) {
        event.preventDefault();
        document.getElementById('btn-play')?.click();
      }
    }
  });
}

// ---------------------------------------------------------------------------
// Build handler — called when user clicks "Build Automata"
// ---------------------------------------------------------------------------

async function handleBuild(tokens, { silent = false } = {}) {
  setBuildStatus('building', 'Building…');

  try {
    const summary = await state.lexer.build(tokens);
    if (!summary.ok) {
      setBuildStatus('error', 'Build failed');
      toast(summary.error || 'Build failed', 'error');
      state.built = false;
      state.lastBuildSummary = null;
      state.tabs.scan?.setBuilt(false);
      state.tabs.nfa?.setBuilt(false);
      state.tabs.dfa?.setBuilt(false);
      return;
    }

    state.built = true;
    state.lastBuildSummary = summary;
    state.tabs.scan?.setBuilt(true);
    state.tabs.nfa?.setBuilt(true);
    state.tabs.dfa?.setBuilt(true);
    state.tabs.step?.setBuilt(true)

    setBuildStatus('ok',
      `DFA: ${summary.dfa_states} states · ${summary.build_ms.toFixed(0)} ms`
    );

    if (!silent) {
      toast(
        `Built DFA with ${summary.dfa_states} states from ${summary.token_count} tokens in ${summary.build_ms.toFixed(0)} ms`,
        'success'
      );
      activateTab('scan');
    }
  } catch (err) {
    setBuildStatus('error', 'Build failed');
    toast('Build failed: ' + err.message, 'error');
    console.error(err);
    state.built = false;
    state.lastBuildSummary = null;
    state.tabs.scan?.setBuilt(false);
    state.tabs.nfa?.setBuilt(false);
    state.tabs.dfa?.setBuilt(false);
    state.tabs.step?.setBuilt(false);
  }
}

// ---------------------------------------------------------------------------
// Kick it off
// ---------------------------------------------------------------------------

bootstrap();
