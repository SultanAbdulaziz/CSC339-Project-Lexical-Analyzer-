/**
 * Tokens tab — editable list of (name, regex) pairs.
 *
 * Order matters: tokens earlier in the list win when multiple regexes match
 * the same longest prefix.
 */
import { DEFAULT_TOKENS, toast, escapeHtml } from '../util.js';

export class TokensTab {
  constructor({ container, onBuild }) {
    this.container = container;
    this.onBuild = onBuild;
    this.tokens = DEFAULT_TOKENS.map(([name, regex]) => ({ name, regex }));
    this.render();
  }

  getTokens() {
    return this.tokens.map(t => ({ ...t }));
  }

  setTokens(arr) {
    this.tokens = arr.map(t => ({ ...t }));
    this.renderRows();
  }

  render() {
    this.container.innerHTML = `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 class="text-lg font-semibold">Token Specifications</h2>
            <p class="text-sm text-stone-500 dark:text-stone-400 mt-1 max-w-2xl">
              Each row defines a token class as a (name, regex) pair.
              <strong class="font-medium text-stone-700 dark:text-stone-300">Order matters</strong> —
              tokens listed earlier win when multiple regexes match the same longest prefix.
            </p>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button id="reset-tokens-btn" class="btn btn-secondary">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
              Reset
            </button>
            <button id="build-btn" class="btn btn-primary">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
              Build Automata
            </button>
          </div>
        </div>

        <!-- Feature reference -->
        <details class="border border-stone-200 dark:border-stone-800 rounded-md text-sm">
          <summary class="px-3 py-2 cursor-pointer select-none font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-900 rounded-md">
            Supported regex features
          </summary>
          <div class="px-3 pb-3 pt-1 text-stone-600 dark:text-stone-400 space-y-1">
            <p><code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">|</code> union, <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">*</code> Kleene star, <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">+</code> positive closure, <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">?</code> optional, <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">( )</code> grouping</p>
            <p>Implicit concatenation: <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">ab</code> means "a then b"</p>
            <p>Escape with <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">\\</code>: <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">\\+ \\* \\(</code></p>
            <p>Character classes: <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">[a-z]</code> <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">[A-Z]</code> <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">[0-9]</code> <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">[A-Za-z]</code> <code class="font-mono text-xs px-1 py-0.5 bg-stone-100 dark:bg-stone-900 rounded">[A-Za-z0-9_]</code></p>
          </div>
        </details>

        <!-- Table -->
        <div class="border border-stone-200 dark:border-stone-800 rounded-md overflow-hidden">
          <div class="grid grid-cols-[36px_3fr_5fr_88px] gap-0 bg-stone-50 dark:bg-stone-900/50 border-b border-stone-200 dark:border-stone-800 text-xs font-medium text-stone-500 dark:text-stone-400 px-1">
            <div class="px-2 py-2">#</div>
            <div class="px-2 py-2">Token name</div>
            <div class="px-2 py-2">Regular expression</div>
            <div class="px-2 py-2 text-right">Actions</div>
          </div>
          <div id="token-rows" class="divide-y divide-stone-100 dark:divide-stone-900"></div>
        </div>

        <!-- Add row -->
        <button id="add-token-btn" class="btn btn-secondary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Add token
        </button>
      </div>
    `;

    this.container.querySelector('#reset-tokens-btn').addEventListener('click', () => {
      if (confirm('Reset all tokens to defaults?')) {
        this.tokens = DEFAULT_TOKENS.map(([name, regex]) => ({ name, regex }));
        this.renderRows();
        toast('Reset to default token set');
      }
    });

    this.container.querySelector('#add-token-btn').addEventListener('click', () => {
      this.tokens.push({ name: '', regex: '' });
      this.renderRows();
      // Focus the new name input
      const lastNameInput = this.container.querySelector(`[data-row="${this.tokens.length - 1}"] [data-field="name"]`);
      if (lastNameInput) lastNameInput.focus();
    });

    this.container.querySelector('#build-btn').addEventListener('click', () => {
      this.onBuild(this.getTokens());
    });

    this.renderRows();
  }

  renderRows() {
    const rowsEl = this.container.querySelector('#token-rows');
    rowsEl.innerHTML = this.tokens.map((tk, i) => this._rowHtml(i, tk)).join('');

    // Wire up handlers
    rowsEl.querySelectorAll('input[data-field]').forEach(input => {
      input.addEventListener('input', e => {
        const row = parseInt(e.target.closest('[data-row]').dataset.row, 10);
        const field = e.target.dataset.field;
        this.tokens[row][field] = e.target.value;
      });
    });
    rowsEl.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', e => {
        const row = parseInt(e.target.closest('[data-row]').dataset.row, 10);
        const action = e.target.closest('[data-action]').dataset.action;
        this._handleAction(row, action);
      });
    });
  }

  _rowHtml(i, tk) {
    return `
      <div data-row="${i}" class="grid grid-cols-[36px_3fr_5fr_88px] items-center gap-0 hover:bg-stone-50/50 dark:hover:bg-stone-900/30 transition-colors">
        <div class="px-3 py-1.5 text-xs text-stone-400 dark:text-stone-500 font-mono text-center">${i + 1}</div>
        <div class="px-1 py-0.5">
          <input data-field="name" class="token-input" type="text" value="${escapeHtml(tk.name)}" placeholder="TOKEN_NAME" autocomplete="off" spellcheck="false">
        </div>
        <div class="px-1 py-0.5">
          <input data-field="regex" class="token-input" type="text" value="${escapeHtml(tk.regex)}" placeholder="regex" autocomplete="off" spellcheck="false">
        </div>
        <div class="px-2 py-0.5 flex items-center justify-end gap-0.5">
          <button data-action="up" title="Move up" class="w-7 h-7 flex items-center justify-center rounded text-stone-400 hover:text-stone-700 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition" ${i === 0 ? 'disabled' : ''}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
          </button>
          <button data-action="down" title="Move down" class="w-7 h-7 flex items-center justify-center rounded text-stone-400 hover:text-stone-700 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition" ${i === this.tokens.length - 1 ? 'disabled' : ''}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
          <button data-action="delete" title="Delete row" class="w-7 h-7 flex items-center justify-center rounded text-stone-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>
    `;
  }

  _handleAction(row, action) {
    if (action === 'up' && row > 0) {
      [this.tokens[row - 1], this.tokens[row]] = [this.tokens[row], this.tokens[row - 1]];
    } else if (action === 'down' && row < this.tokens.length - 1) {
      [this.tokens[row + 1], this.tokens[row]] = [this.tokens[row], this.tokens[row + 1]];
    } else if (action === 'delete') {
      this.tokens.splice(row, 1);
    }
    this.renderRows();
  }
}
