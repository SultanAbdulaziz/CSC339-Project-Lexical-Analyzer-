/**
 * Step-by-step scanner visualization tab.
 * Uses a pre-computed "Timeline Graph" to incrementally unhide the execution path.
 */
import { toast, escapeHtml, highlightSource, colorFor, isDark } from '../util.js';
import { renderDot } from '../graph.js';

export class StepTab {
  constructor({ container, getLexer, isBuilt }) {
    this.container = container;
    this.getLexer = getLexer;
    this.isBuilt = isBuilt;
    this.state = null;      
    this.isActive = false;  
    this.baseSource = '';
    this.isPlaying = false;
    this.playTimer = null;
    this.playDelay = 450;
    this.lastLoggedStep = -1;
    this.finishedNotified = false;
    this.render();
  }

  setBuilt(built) {
    if (!built) this._stopPlayback();
    this.isBuilt = built;
    this.render();
  }

  onShow() {
    // If the tab is opened while active, ensure the graph view catches up
    if (this.isActive && this.state) {
      this._updateGraphVisibility(this.state.step_count);
    }
  }

  render() {
    if (!this.isBuilt) {
      this.container.innerHTML = `
        <div class="flex flex-col items-center justify-center py-24 text-center">
          <div class="w-12 h-12 rounded-full bg-stone-100 dark:bg-stone-900 flex items-center justify-center mb-4">
            <svg class="text-stone-400" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          </div>
          <p class="text-sm text-stone-500 dark:text-stone-400">Build the automata from the Tokens tab first.</p>
        </div>`;
      return;
    }

    this.container.innerHTML = `
      <div class="space-y-6">
        <div>
          <h2 class="text-lg font-semibold">Execution Timeline</h2>
          <p class="text-sm text-stone-500 dark:text-stone-400 mt-1">
            Watch the maximal-munch algorithm traverse the input. The graph unrolls chronologically, showing the exact path taken.
          </p>
        </div>

        <div class="grid lg:grid-cols-[380px_1fr] gap-6">
          <div class="space-y-4">
            <div class="p-4 rounded-md border border-stone-200 dark:border-stone-800 bg-stone-50/50 dark:bg-stone-900/30 flex flex-wrap gap-2 items-center">
              <button id="btn-init" class="btn btn-primary w-full justify-center mb-2">Start Debugger</button>
              <div class="grid grid-cols-2 gap-2 w-full">
                <button id="btn-play" class="btn btn-secondary text-xs" disabled>Play</button>
                <button id="btn-step" class="btn btn-secondary text-xs" disabled>Step</button>
                <button id="btn-next" class="btn btn-secondary text-xs" disabled>Run Token</button>
                <button id="btn-end" class="btn btn-secondary text-xs" disabled>Run All</button>
              </div>
              <label class="w-full flex items-center justify-between gap-3 mt-2 text-xs text-stone-500 dark:text-stone-400">
                <span>Playback speed</span>
                <select id="step-speed" class="px-2 py-1 rounded border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-stone-700 dark:text-stone-300">
                  <option value="800">0.5×</option>
                  <option value="450" selected>1×</option>
                  <option value="220">2×</option>
                  <option value="90">4×</option>
                </select>
              </label>
              <button id="btn-reset" class="btn btn-secondary w-full justify-center mt-2 hidden text-xs text-red-600 dark:text-red-400">Stop / Reset</button>
            </div>

            <div>
              <label class="text-sm font-medium text-stone-700 dark:text-stone-300 mb-1.5 block">Source Tape</label>
              <textarea id="step-source" class="w-full h-32 p-3 rounded-md border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 focus:outline-none focus:border-accent-600 font-mono text-sm resize-y" spellcheck="false">int x = 5;</textarea>
              <div id="step-highlight" class="hidden w-full h-32 p-3 rounded-md border border-stone-200 dark:border-stone-800 bg-stone-100 dark:bg-stone-900 overflow-y-auto font-mono text-sm leading-relaxed tracking-wide"></div>
            </div>

            <div>
              <label class="text-sm font-medium text-stone-700 dark:text-stone-300 mb-1.5 block">Event Log</label>
              <div id="step-event" class="w-full h-24 p-3 rounded-md border border-stone-200 dark:border-stone-800 bg-stone-50/50 dark:bg-stone-900/50 overflow-y-auto font-mono text-xs text-stone-600 dark:text-stone-400">
                Waiting to start...
              </div>
            </div>

            <div>
              <label class="text-sm font-medium text-stone-700 dark:text-stone-300 mb-1.5 block">Emitted Tokens</label>
              <div id="step-tokens" class="w-full min-h-[160px] max-h-[300px] rounded-md border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 overflow-y-auto subtle-scroll">
                 <div class="p-4 text-center text-xs text-stone-400">No tokens emitted yet.</div>
              </div>
            </div>
          </div>

          <div>
            <div id="step-graph-container" class="relative w-full bg-stone-50/50 dark:bg-stone-950/30 border border-stone-200 dark:border-stone-800 rounded-md overflow-hidden" style="height:680px;">
              <div class="absolute inset-0 flex items-center justify-center text-sm text-stone-400">Ready to trace.</div>
            </div>
            <div class="flex items-center justify-between mt-2">
               <p class="text-xs text-stone-400 dark:text-stone-500">Pan/Zoom to explore the chronological path.</p>
               <span id="step-counter" class="text-xs font-mono text-stone-500">Steps: 0</span>
            </div>
          </div>
        </div>
      </div>
    `;

    this._bindEvents();
  }

  _bindEvents() {
    const q = sel => this.container.querySelector(sel);
    
    q('#btn-init').addEventListener('click', async () => {
      const source = q('#step-source').value;
      if (!source.trim()) return toast('Enter source text first', 'error');
      
      this.baseSource = source;
      this.lastLoggedStep = -1;
      this.finishedNotified = false;
      
      // 1. Generate and Render the Timeline Graph Upfront
      await this._renderTimelineGraph(source);

      // 2. Initialize the Stepper State
      const res = await this.getLexer().stepInit(source);
      if (res.error) return toast(res.error, 'error');
      
      this.state = res;
      this.isActive = true;
      this._togglePlaybackMode(true);
      this._updateUI();
    });

    q('#btn-play').addEventListener('click', () => this._togglePlayback());

    q('#btn-step').addEventListener('click', async () => {
      this._stopPlayback();
      this.state = await this.getLexer().stepAdvance();
      this._updateUI();
    });

    q('#btn-next').addEventListener('click', async () => {
      this._stopPlayback();
      this.state = await this.getLexer().stepRunToNextToken();
      this._updateUI();
    });

    q('#btn-end').addEventListener('click', async () => {
      this._stopPlayback();
      this.state = await this.getLexer().stepRunToEnd();
      this._updateUI();
    });

    q('#step-speed').addEventListener('change', event => {
      this.playDelay = Number(event.target.value);
      if (this.isPlaying) {
        this._stopPlayback();
        this._togglePlayback();
      }
    });

    q('#btn-reset').addEventListener('click', () => {
      this._stopPlayback();
      this.isActive = false;
      this.state = null;
      this._togglePlaybackMode(false);
      this.container.querySelector('#step-graph-container').innerHTML = 
        `<div class="absolute inset-0 flex items-center justify-center text-sm text-stone-400">Ready to trace.</div>`;
    });
  }

  _togglePlaybackMode(active) {
    const q = sel => this.container.querySelector(sel);
    q('#step-source').classList.toggle('hidden', active);
    q('#step-highlight').classList.toggle('hidden', !active);
    q('#btn-init').classList.toggle('hidden', active);
    q('#btn-reset').classList.toggle('hidden', !active);
    
    ['#btn-play', '#btn-step', '#btn-next', '#btn-end'].forEach(id => {
      q(id).disabled = !active;
    });

    if (active) {
      q('#step-event').innerHTML = ''; // Clear log on start
    }
  }

  _togglePlayback() {
    if (!this.isActive || !this.state || this._isComplete()) return;
    if (this.isPlaying) {
      this._stopPlayback();
      return;
    }
    this.isPlaying = true;
    this._updatePlayButton();
    this._playNext();
  }

  _stopPlayback() {
    this.isPlaying = false;
    if (this.playTimer) clearTimeout(this.playTimer);
    this.playTimer = null;
    this._updatePlayButton();
  }

  _updatePlayButton() {
    const btn = this.container?.querySelector('#btn-play');
    if (!btn) return;
    btn.textContent = this.isPlaying ? 'Pause' : 'Play';
    btn.setAttribute('aria-pressed', this.isPlaying ? 'true' : 'false');
  }

  async _playNext() {
    if (!this.isPlaying || this._isComplete()) {
      this._stopPlayback();
      return;
    }
    this.state = await this.getLexer().stepAdvance();
    this._updateUI();
    if (!this.isPlaying || this._isComplete()) {
      this._stopPlayback();
      return;
    }
    this.playTimer = setTimeout(() => this._playNext(), this.playDelay);
  }

  _isComplete() {
    if (!this.state) return false;
    return Boolean(this.state.error) ||
      (this.state.pos >= this.state.source_len && this.state.inner_i === 0) ||
      String(this.state.last_event || '').includes('Completed');
  }

  async _renderTimelineGraph(source) {
    const container = this.container.querySelector('#step-graph-container');
    container.innerHTML = `
      <div class="absolute inset-0 flex items-center justify-center text-stone-400">
        <span class="flex items-center gap-2">
          <svg class="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          Generating Timeline Trace...
        </span>
      </div>`;

    try {
      const dot = await this.getLexer().stepTraceDot(source);
      console.log("Generated DOT String:\n", dot);
      await renderDot(container, dot, { panZoom: true });
    } catch (err) {
      console.error(err);
      toast("Timeline graph failed to render", "error");
    }
  }

  async _updateUI() {
    if (!this.state) return;
    const q = sel => this.container.querySelector(sel);
    const { pos, inner_i, tokens, last_event, step_count, source_len } = this.state;

    // Highlight Tape & Cursor
    const cursorIndex = Math.min(pos + inner_i, source_len);
    q('#step-highlight').innerHTML = highlightSource(this.baseSource, tokens, { cursorPos: cursorIndex });

    // Event Log
    const log = q('#step-event');
    if (step_count !== this.lastLoggedStep) {
      const time = new Date().toLocaleTimeString([], {hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit'});
      const tone = this.state.error ? 'text-red-600 dark:text-red-400' : 'text-accent-600 dark:text-accent-400';
      log.innerHTML = `<div class="mb-1 ${tone}">[${time}] ${escapeHtml(last_event)}</div>` + log.innerHTML;
      this.lastLoggedStep = step_count;
    }

    // Tokens Table
    if (tokens.length > 0) {
      q('#step-tokens').innerHTML = `
        <table class="w-full text-left text-xs">
          <thead class="bg-stone-50 dark:bg-stone-900 text-stone-500 sticky top-0">
            <tr><th class="px-3 py-1.5 font-medium">Lexeme</th><th class="px-3 py-1.5 font-medium">Token</th></tr>
          </thead>
          <tbody class="divide-y divide-stone-100 dark:divide-stone-800">
            ${tokens.map(tk => {
              const c = colorFor(tk.token);
              const bg = isDark() ? c.dark : c.bg;
              const fg = isDark() ? c.darkText : c.text;
              return `<tr>
                <td class="px-3 py-1.5 font-mono">${escapeHtml(tk.lexeme)}</td>
                <td class="px-3 py-1.5"><span class="px-1.5 py-0.5 rounded font-mono" style="background:${bg};color:${fg};">${escapeHtml(tk.token)}</span></td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>`;
    }

    q('#step-counter').textContent = `Steps: ${step_count}`;

    // Incremental Reveal & Highlight Logic
    this._updateGraphVisibility(step_count);

    // End State check
    if (this._isComplete()) {
      this._stopPlayback();
      if (!this.finishedNotified) {
        toast(this.state.error ? this.state.error : 'Scanning complete!', this.state.error ? 'error' : 'success');
        this.finishedNotified = true;
      }
      ['#btn-play', '#btn-step', '#btn-next', '#btn-end'].forEach(id => q(id).disabled = true);
    }
  }

  // The core logic that unhides the chronological path up to the current step
  _updateGraphVisibility(currentStep) {
    const svg = this.container.querySelector('#step-graph-container svg');
    if (!svg) return;

    // 1. Process Nodes
    svg.querySelectorAll('g.node').forEach(node => {
      const title = node.querySelector('title')?.textContent || '';
      const match = title.match(/step_(\d+)/);
      if (!match) return;
      
      const stepIdx = parseInt(match[1], 10);
      
      // Hide future nodes, reveal past/present nodes
      node.style.opacity = stepIdx > currentStep ? '0' : '1';
      node.style.transition = 'opacity 0.2s ease-in-out';
      node.classList.toggle('is-current-step', stepIdx === currentStep);

      // Highlight the active (current) node
      const shape = node.querySelector('ellipse, polygon');
      if (shape) {
        // Cache original colors to restore them when the node is no longer active
        if (!shape.hasAttribute('data-orig-fill')) {
          shape.setAttribute('data-orig-fill', shape.getAttribute('fill'));
          shape.setAttribute('data-orig-stroke', shape.getAttribute('stroke'));
        }

        if (stepIdx === currentStep) {
          shape.setAttribute('fill', '#fef3c7');     // amber-100 highlight
          shape.setAttribute('stroke', '#f59e0b');   // amber-500 border
          shape.setAttribute('stroke-width', '3');
        } else {
          shape.setAttribute('fill', shape.getAttribute('data-orig-fill'));
          shape.setAttribute('stroke', shape.getAttribute('data-orig-stroke'));
          shape.setAttribute('stroke-width', '1');
        }
      }
    });

    // 2. Process Edges
    svg.querySelectorAll('g.edge').forEach(edge => {
      const title = edge.querySelector('title')?.textContent || '';
      // Edge format: step_X->step_Y (Y is the target node)
      const match = title.match(/step_\d+->step_(\d+)/);
      if (!match) return;
      
      const targetIdx = parseInt(match[1], 10);
      
      // An edge is only visible if the target node has been reached
      edge.style.opacity = targetIdx > currentStep ? '0' : '1';
      edge.style.transition = 'opacity 0.2s ease-in-out';
    });
  }
}
