/**
 * Scan tab — source editor + tokenize + token table + highlighted source.
 */
import {
  DEFAULT_PROGRAM, toast, escapeHtml,
  highlightSource, tokenLegend, colorFor, isDark,
} from '../util.js';

export class ScanTab {
  constructor({ container, getLexer, isBuilt }) {
    this.container = container;
    this.getLexer = getLexer;
    this.isBuilt = isBuilt;
    this.source = DEFAULT_PROGRAM;
    this.lastResult = null;
    this.render();
  }

  setBuilt(built) {
    this.isBuilt = built;
    const btn = this.container.querySelector('#scan-btn');
    if (btn) btn.disabled = !built;
    const msg = this.container.querySelector('#scan-needs-build');
    if (msg) msg.classList.toggle('hidden', built);
  }

  render() {
    this.container.innerHTML = `
      <div class="space-y-6">
        <!-- Header -->
        <div>
          <h2 class="text-lg font-semibold">Tokenize a Program</h2>
          <p class="text-sm text-stone-500 dark:text-stone-400 mt-1">
            Scan source text left-to-right using maximal-munch. Each emitted token shows its
            lexeme, class, and source position.
          </p>
        </div>

        <div id="scan-needs-build" class="hidden p-3 rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 text-sm text-amber-800 dark:text-amber-300">
          Build the automata first — go to the <strong>Tokens</strong> tab and click <em>Build Automata</em>.
        </div>

        <!-- Editor + output grid -->
        <div class="grid lg:grid-cols-2 gap-4">
          <!-- Source editor -->
          <div class="flex flex-col">
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-stone-700 dark:text-stone-300">Source</label>
              <button id="reset-source-btn" class="text-xs text-stone-500 hover:text-stone-900 dark:hover:text-stone-100 transition">
                Reset to example
              </button>
            </div>
            <textarea id="source-editor"
              class="source-area w-full flex-1 min-h-[280px] p-3 rounded-md border border-stone-200 dark:border-stone-800 bg-stone-50/50 dark:bg-stone-900/50 focus:outline-none focus:border-accent-600 focus:bg-white dark:focus:bg-stone-950 subtle-scroll resize-y"
              spellcheck="false" autocomplete="off" autocorrect="off"
            ></textarea>
            <div class="mt-3 flex items-center gap-2">
              <button id="scan-btn" class="btn btn-primary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Tokenize
              </button>
              <span id="scan-stats" class="text-xs text-stone-500 dark:text-stone-400"></span>
            </div>
          </div>

          <!-- Output -->
          <div class="flex flex-col">
            <label class="text-sm font-medium text-stone-700 dark:text-stone-300 mb-2">Tokens</label>
            <div id="scan-output" class="flex-1 min-h-[280px] border border-stone-200 dark:border-stone-800 rounded-md overflow-hidden">
              <div class="h-full flex items-center justify-center text-sm text-stone-400 dark:text-stone-500 px-6 text-center">
                Click <span class="font-mono text-xs px-1.5 py-0.5 mx-1 bg-stone-100 dark:bg-stone-900 rounded">Tokenize</span> to scan the source.
              </div>
            </div>
          </div>
        </div>

        <!-- Highlighted source view -->
        <div>
          <h3 class="text-sm font-medium text-stone-700 dark:text-stone-300 mb-2">Highlighted source</h3>
          <div id="highlight-view" class="text-sm text-stone-400 dark:text-stone-500 italic">
            (Run a scan to see token highlights here.)
          </div>
        </div>
      </div>
    `;

    this.container.querySelector('#source-editor').value = this.source;
    this.container.querySelector('#source-editor').addEventListener('input', e => {
      this.source = e.target.value;
    });

    this.container.querySelector('#reset-source-btn').addEventListener('click', () => {
      this.source = DEFAULT_PROGRAM;
      this.container.querySelector('#source-editor').value = this.source;
    });

    this.container.querySelector('#scan-btn').addEventListener('click', () => this._runScan());
    this.setBuilt(this.isBuilt);
  }

  async _runScan() {
    if (!this.isBuilt) return;
    const lexer = this.getLexer();
    if (!lexer) return;

    const btn = this.container.querySelector('#scan-btn');
    btn.disabled = true;
    btn.textContent = 'Scanning…';
    const t0 = performance.now();

    try {
      const result = await lexer.scan(this.source);
      const elapsed = performance.now() - t0;
      this.lastResult = result;
      this._renderResult(result, elapsed);
    } catch (err) {
      toast('Scan failed: ' + err.message, 'error');
      console.error(err);
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg> Tokenize`;
    }
  }

  _renderResult(result, elapsed) {
    const outputEl = this.container.querySelector('#scan-output');
    const statsEl = this.container.querySelector('#scan-stats');
    const highlightEl = this.container.querySelector('#highlight-view');

    if (result.error) {
      statsEl.innerHTML = `<span class="text-red-600 dark:text-red-400">Error</span>`;
      outputEl.innerHTML = `
        <div class="h-full p-6 flex flex-col items-center justify-center text-center">
          <svg class="text-red-500 mb-3" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <p class="text-sm font-medium text-red-700 dark:text-red-400 mb-1">${escapeHtml(result.error)}</p>
          ${result.tokens.length > 0 ? `<p class="text-xs text-stone-500 mt-2">${result.tokens.length} token(s) emitted before the error.</p>` : ''}
        </div>
      `;
    } else {
      statsEl.innerHTML = `
        <span class="text-emerald-600 dark:text-emerald-400">✓</span>
        <span>${result.tokens.length} tokens · ${elapsed.toFixed(0)} ms</span>
      `;
    }

    // Token table (even on error, show what was emitted)
    if (result.tokens.length > 0) {
      const tableHtml = `
        <div class="overflow-auto subtle-scroll max-h-[450px]">
          <table class="w-full text-sm">
            <thead class="bg-stone-50 dark:bg-stone-900/50 text-stone-500 dark:text-stone-400 text-xs sticky top-0 backdrop-blur-sm">
              <tr>
                <th class="px-3 py-2 text-left font-medium">Lexeme</th>
                <th class="px-3 py-2 text-left font-medium">Token</th>
                <th class="px-3 py-2 text-right font-medium">Line</th>
                <th class="px-3 py-2 text-right font-medium pr-4">Col</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-100 dark:divide-stone-900">
              ${result.tokens.map(tk => {
                const c = colorFor(tk.token);
                const dark = isDark();
                const bg = dark ? c.dark : c.bg;
                const fg = dark ? c.darkText : c.text;
                return `
                  <tr class="hover:bg-stone-50 dark:hover:bg-stone-900/30">
                    <td class="px-3 py-1.5 font-mono text-[13px]">${escapeHtml(tk.lexeme)}</td>
                    <td class="px-3 py-1.5">
                      <span class="inline-block px-1.5 py-0.5 rounded text-[11px] font-mono" style="background:${bg};color:${fg};">${escapeHtml(tk.token)}</span>
                    </td>
                    <td class="px-3 py-1.5 text-right font-mono text-xs text-stone-500">${tk.line}</td>
                    <td class="px-3 py-1.5 text-right font-mono text-xs text-stone-500 pr-4">${tk.col}</td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;
      if (!result.error) {
        outputEl.innerHTML = tableHtml;
      } else {
        // append the table below the error
        outputEl.innerHTML += tableHtml;
      }
    }

    // Highlighted source
    if (result.tokens.length > 0) {
      const html = highlightSource(this.source, result.tokens);
      const legend = tokenLegend(result.tokens);
      highlightEl.innerHTML = `
        <div class="p-4 rounded-md border border-stone-200 dark:border-stone-800 bg-stone-50/50 dark:bg-stone-900/30 source-area leading-relaxed">${html}</div>
        ${legend ? `<div class="mt-3 flex flex-wrap">${legend}</div>` : ''}
      `;
    }
  }
}
