/**
 * DFA tab — visualize the result of subset construction.
 */
import { toast } from '../util.js';
import { renderDot, downloadSvg } from '../graph.js';

export class DfaTab {
  constructor({ container, getLexer, isBuilt, getStats }) {
    this.container = container;
    this.getLexer = getLexer;
    this.isBuilt = isBuilt;
    this.getStats = getStats;
    this.maxStates = 80;
    this.hideTrap = true;
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

  _statCard(label, value) {
    return `
      <div class="px-3 py-2.5 rounded-md border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950">
        <div class="text-[11px] uppercase tracking-wide text-stone-500 dark:text-stone-400">${label}</div>
        <div class="text-xl font-semibold font-mono mt-0.5">${value}</div>
      </div>`;
  }

  _render() {
    if (!this.isBuilt) {
      this.container.innerHTML = `
        <div class="flex flex-col items-center justify-center py-24 text-center">
          <div class="w-12 h-12 rounded-full bg-stone-100 dark:bg-stone-900 flex items-center justify-center mb-4">
            <svg class="text-stone-400" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg>
          </div>
          <p class="text-sm text-stone-500 dark:text-stone-400">Build the automata from the Tokens tab first.</p>
        </div>`;
      return;
    }

    const s = this.getStats() || {};
    this.container.innerHTML = `
      <div class="space-y-6">
        <div>
          <h2 class="text-lg font-semibold">DFA Visualization</h2>
          <p class="text-sm text-stone-500 dark:text-stone-400 mt-1 max-w-2xl">
            The deterministic finite automaton built from the combined NFA via subset construction.
            Accepting states (double circle) are labeled with the token they emit, resolved by your
            priority order.
          </p>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          ${this._statCard('DFA states', s.dfa_states ?? '—')}
          ${this._statCard('Accepting', s.accept_states ?? '—')}
          ${this._statCard('Alphabet', s.alphabet_size ?? '—')}
          ${this._statCard('Build time', s.build_ms != null ? Math.round(s.build_ms) + ' ms' : '—')}
        </div>

        <div class="grid lg:grid-cols-[260px_1fr] gap-6">
          <!-- Sidebar -->
          <div class="space-y-5">
            <div>
              <div class="flex justify-between mb-1.5">
                <label class="text-sm font-medium">Max states rendered</label>
                <span id="dfa-max-val" class="text-xs font-mono text-stone-500">${this.maxStates}</span>
              </div>
              <input id="dfa-max-slider" type="range" min="10" max="300" step="10" value="${this.maxStates}" class="w-full accent-accent-600">
            </div>

            <label class="flex items-center gap-2.5 cursor-pointer text-sm select-none">
              <input id="dfa-hide-trap" type="checkbox" ${this.hideTrap ? 'checked' : ''} class="w-4 h-4 rounded accent-accent-600">
              Hide trap state
            </label>
            <p class="text-xs text-stone-500 dark:text-stone-400 -mt-3">The dead state for invalid transitions — hiding it keeps the diagram readable.</p>

            <div class="text-xs space-y-1.5 pt-3 border-t border-stone-200 dark:border-stone-800 text-stone-500 dark:text-stone-400">
              <div class="flex justify-between"><span>Reachable</span><span id="dfa-total" class="font-mono text-stone-700 dark:text-stone-300">—</span></div>
              <div class="flex justify-between"><span>Showing</span><span id="dfa-shown" class="font-mono text-stone-700 dark:text-stone-300">—</span></div>
            </div>

            <div class="flex flex-col gap-2 pt-3 border-t border-stone-200 dark:border-stone-800">
              <button id="dfa-dl" class="btn btn-secondary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Download SVG
              </button>
            </div>

            <div class="text-xs pt-3 border-t border-stone-200 dark:border-stone-800 space-y-1.5 text-stone-500 dark:text-stone-400">
              <div class="flex items-center gap-2"><span class="w-3 h-3 inline-block rounded-full border border-stone-400 bg-stone-100 dark:bg-stone-800"></span>Plain state (S0, S1, …)</div>
              <div class="flex items-center gap-2"><span class="w-3 h-3 inline-block rounded-full border-2 border-emerald-600 bg-emerald-50 dark:bg-emerald-950"></span>Accepting state (token labeled)</div>
              <p>States labeled in BFS order from initial.</p>
            </div>
          </div>

          <!-- Graph -->
          <div>
            <div id="dfa-graph-container"
              class="relative w-full bg-stone-50/50 dark:bg-stone-900/30 border border-stone-200 dark:border-stone-800 rounded-md overflow-hidden"
              style="height:560px;">
              <div class="absolute inset-0 flex items-center justify-center text-sm text-stone-400 dark:text-stone-500 pointer-events-none">
                Building graph…
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
          <pre id="dfa-dot-src" class="px-3 pb-3 pt-1 text-xs font-mono text-stone-600 dark:text-stone-400 overflow-x-auto subtle-scroll max-h-64 whitespace-pre-wrap"></pre>
        </details>
      </div>`;

    const slider = this.container.querySelector('#dfa-max-slider');
    const sliderVal = this.container.querySelector('#dfa-max-val');
    slider.addEventListener('input', e => { sliderVal.textContent = e.target.value; });
    slider.addEventListener('change', e => {
      this.maxStates = parseInt(e.target.value, 10);
      this._renderGraph();
    });

    this.container.querySelector('#dfa-hide-trap').addEventListener('change', e => {
      this.hideTrap = e.target.checked;
      this._renderGraph();
    });

    this.container.querySelector('#dfa-dl').addEventListener('click', () => {
      downloadSvg(this.container.querySelector('#dfa-graph-container'), 'dfa.svg');
    });
  }

  async _renderGraph() {
    if (!this.isBuilt) return;
    const lexer = this.getLexer();
    if (!lexer) return;

    const containerEl = this.container.querySelector('#dfa-graph-container');
    if (!containerEl) return;

    containerEl.innerHTML = `
      <div class="absolute inset-0 flex items-center justify-center text-sm text-stone-400 dark:text-stone-500 pointer-events-none">
        <span class="flex items-center gap-2">
          <svg class="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
          Rendering DFA…
        </span>
      </div>`;

    try {
      const dot = await lexer.dfaDot({
        maxStates: this.maxStates,
        hideTrap: this.hideTrap,
        highlightStateId: null,
      });
      this.lastDot = dot;
      await renderDot(containerEl, dot, { panZoom: true });

      const m = dot.match(/Showing first (\d+) of (\d+) states/);
      const shown = m ? m[1] : (dot.match(/^\s+n\d+\s*\[/gm) || []).length;
      const total = m ? m[2] : shown;
      this.container.querySelector('#dfa-total').textContent = total;
      this.container.querySelector('#dfa-shown').textContent = shown;

      const src = this.container.querySelector('#dfa-dot-src');
      if (src) src.textContent = dot;
    } catch (err) {
      toast('DFA render failed: ' + err.message, 'error');
      console.error('DFA render error:', err);
    }
  }
}
