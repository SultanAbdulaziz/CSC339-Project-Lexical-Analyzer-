/**
 * NFA tab — visualize Thompson's-constructed ε-NFAs via @viz-js/viz.
 */
import { toast, escapeHtml } from '../util.js';
import { renderDot, downloadSvg } from '../graph.js';

export class NfaTab {
  constructor({ container, getLexer, isBuilt, getTokens }) {
    this.container = container;
    this.getLexer = getLexer;
    this.isBuilt = isBuilt;
    this.getTokens = getTokens;
    this.currentToken = null;   // null => combined NFA
    this.maxStates = 60;
    this.lastDot = '';
    this._render();
  }

  setBuilt(built) {
    this.isBuilt = built;
    this._render();
    if (built) {
      // Only render immediately if the tab container is visible;
      // otherwise clear lastDot so onShow() triggers a fresh render.
      if (this.container.offsetParent !== null) {
        this._renderGraph();
      } else {
        this.lastDot = '';
      }
    }
  }

  onShow() {
    if (this.isBuilt && !this.lastDot) this._renderGraph();
  }

  _render() {
    if (!this.isBuilt) {
      this.container.innerHTML = `
        <div class="flex flex-col items-center justify-center py-24 text-center">
          <div class="w-12 h-12 rounded-full bg-stone-100 dark:bg-stone-900 flex items-center justify-center mb-4">
            <svg class="text-stone-400" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="12" cy="18" r="3"/><line x1="8.5" y1="7.5" x2="11" y2="15.5"/><line x1="15.5" y1="7.5" x2="13" y2="15.5"/></svg>
          </div>
          <p class="text-sm text-stone-500 dark:text-stone-400">Build the automata from the Tokens tab first.</p>
        </div>`;
      return;
    }

    const tokens = this.getTokens();
    const options = [
      `<option value="__combined__">⋃ Combined NFA</option>`,
      ...tokens.map(t =>
        `<option value="${escapeHtml(t.name)}"${t.name === this.currentToken ? ' selected' : ''}>${escapeHtml(t.name)}</option>`
      )
    ].join('');

    this.container.innerHTML = `
      <div class="space-y-6">
        <div>
          <h2 class="text-lg font-semibold">NFA Visualization</h2>
          <p class="text-sm text-stone-500 dark:text-stone-400 mt-1 max-w-2xl">
            Each token regex is converted to an ε-NFA via Thompson's construction, then all NFAs
            are unified into a single combined NFA with one start state.
          </p>
        </div>

        <div class="grid lg:grid-cols-[260px_1fr] gap-6">
          <!-- Sidebar -->
          <div class="space-y-5">
            <div>
              <label class="block text-sm font-medium mb-1.5">Show NFA for</label>
              <select id="nfa-token-select" class="w-full px-3 py-2 text-sm rounded-md border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 focus:outline-none focus:border-accent-600 font-mono">
                ${options}
              </select>
            </div>

            <div>
              <div class="flex justify-between mb-1.5">
                <label class="text-sm font-medium">Max states rendered</label>
                <span id="nfa-max-val" class="text-xs font-mono text-stone-500">${this.maxStates}</span>
              </div>
              <input id="nfa-max-slider" type="range" min="10" max="500" step="10" value="${this.maxStates}" class="w-full accent-accent-600">
              <p class="text-xs text-stone-500 dark:text-stone-400 mt-1">The ID regex produces 450+ states after expansion. Lower limit keeps rendering fast.</p>
            </div>

            <div class="text-xs space-y-1.5 pt-3 border-t border-stone-200 dark:border-stone-800 text-stone-500 dark:text-stone-400">
              <div class="flex justify-between"><span>Total states</span><span id="nfa-total" class="font-mono text-stone-700 dark:text-stone-300">—</span></div>
              <div class="flex justify-between"><span>Showing</span><span id="nfa-shown" class="font-mono text-stone-700 dark:text-stone-300">—</span></div>
            </div>

            <div class="flex flex-col gap-2 pt-3 border-t border-stone-200 dark:border-stone-800">
              <button id="nfa-dl" class="btn btn-secondary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Download SVG
              </button>
            </div>

            <div class="text-xs pt-3 border-t border-stone-200 dark:border-stone-800 space-y-1.5 text-stone-500 dark:text-stone-400">
              <div class="flex items-center gap-2"><span class="w-3 h-3 inline-block rounded-full border border-stone-400 bg-stone-100 dark:bg-stone-800"></span>Plain state</div>
              <div class="flex items-center gap-2"><span class="w-3 h-3 inline-block rounded-full border-2 border-emerald-600 bg-emerald-50 dark:bg-emerald-950"></span>Accept state (labeled with token)</div>
              <div class="flex items-center gap-2"><span class="w-5 border-t border-dashed border-stone-400 inline-block"></span>ε-transition</div>
            </div>
          </div>

          <!-- Graph -->
          <div>
            <div id="nfa-graph-container"
              class="relative w-full bg-stone-50/50 dark:bg-stone-900/30 border border-stone-200 dark:border-stone-800 rounded-md overflow-hidden"
              style="height:520px;">
              <div id="nfa-placeholder" class="absolute inset-0 flex items-center justify-center text-sm text-stone-400 dark:text-stone-500 pointer-events-none">
                Select a token to visualize its NFA.
              </div>
            </div>
            <p class="mt-2 text-xs text-stone-400 dark:text-stone-500">
              Scroll to zoom · drag to pan · double-click to reset view
            </p>
          </div>
        </div>

        <details class="border border-stone-200 dark:border-stone-800 rounded-md text-sm">
          <summary class="px-3 py-2 cursor-pointer select-none font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-900 rounded-md">
            DOT source
          </summary>
          <pre id="nfa-dot-src" class="px-3 pb-3 pt-1 text-xs font-mono text-stone-600 dark:text-stone-400 overflow-x-auto subtle-scroll max-h-64 whitespace-pre-wrap"></pre>
        </details>
      </div>`;

    this.container.querySelector('#nfa-token-select').addEventListener('change', e => {
      const v = e.target.value;
      this.currentToken = v === '__combined__' ? null : v;
      this._renderGraph();
    });

    const slider = this.container.querySelector('#nfa-max-slider');
    const sliderVal = this.container.querySelector('#nfa-max-val');
    slider.addEventListener('input', e => { sliderVal.textContent = e.target.value; });
    slider.addEventListener('change', e => {
      this.maxStates = parseInt(e.target.value, 10);
      this._renderGraph();
    });

    this.container.querySelector('#nfa-dl').addEventListener('click', () => {
      const name = this.currentToken || 'combined';
      downloadSvg(this.container.querySelector('#nfa-graph-container'), `nfa-${name}.svg`);
    });
  }

  async _renderGraph() {
    if (!this.isBuilt) return;
    const lexer = this.getLexer();
    if (!lexer) return;

    const containerEl = this.container.querySelector('#nfa-graph-container');
    if (!containerEl) return;

    // Show a loading indicator — renderDot will clear it when done
    containerEl.innerHTML = `
      <div class="absolute inset-0 flex items-center justify-center text-sm text-stone-400 dark:text-stone-500 pointer-events-none">
        <span class="flex items-center gap-2">
          <svg class="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
          Rendering NFA…
        </span>
      </div>`;

    try {
      const dot = await lexer.nfaDot(this.currentToken, this.maxStates);
      this.lastDot = dot;
      await renderDot(containerEl, dot, { panZoom: true });

      // Update stats from DOT annotation
      const m = dot.match(/Showing first (\d+) of (\d+) states/);
      const shown = m ? m[1] : (dot.match(/^\s+n\d+\s*\[/gm) || []).length;
      const total = m ? m[2] : shown;
      this.container.querySelector('#nfa-total').textContent = total;
      this.container.querySelector('#nfa-shown').textContent = shown;

      const src = this.container.querySelector('#nfa-dot-src');
      if (src) src.textContent = dot;
    } catch (err) {
      toast('NFA render failed: ' + err.message, 'error');
      console.error('NFA render error:', err);
    }
  }
}
