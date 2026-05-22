/**
 * Shared utilities used across tabs.
 */

// ---------------------------------------------------------------------------
// Defaults
// ---------------------------------------------------------------------------

export const DEFAULT_TOKENS = [
  ['KW_IF', 'if'],
  ['KW_THEN', 'then'],
  ['KW_ELSE', 'else'],
  ['KW_WHILE', 'while'],
  ['KW_FOR', 'for'],
  ['KW_RETURN', 'return'],
  ['KW_CONTINUE', 'continue'],
  ['KW_BREAK', 'break'],
  ['KW_INT', 'int'],
  ['KW_FLOAT', 'float'],
  ['ID', '[A-Za-z][A-Za-z0-9_]*'],
  ['NUM', '[0-9]+(\\.[0-9]+)?'],
  ['EQ', '=='],
  ['NEQ', '!='],
  ['LEQ', '<='],
  ['GEQ', '>='],
  ['ASSIGN', '='],
  ['LT', '<'],
  ['GT', '>'],
  ['OP_PLUS', '\\+'],
  ['OP_MINUS', '-'],
  ['OP_MUL', '\\*'],
  ['OP_DIV', '/'],
  ['LPAREN', '\\('],
  ['RPAREN', '\\)'],
  ['LBRACE', '{'],
  ['RBRACE', '}'],
  ['SEMI', ';'],
  ['COMMA', ','],
  ['PERIOD', '\\.'],
];

export const DEFAULT_PROGRAM = `int my_var = 10 ;
float x = 3.14 ;
for ( int i = 0 , i < 10 ; i = i + 1.5 ) {
    while ( i <= 5 ) {
        if ( x == 3.14 ) then {
            x = x * 2.0 / 1.5 - 0.5 ;
            continue ;
        } else {
            if ( x != 0.0 ) break ;
        }
    }
}
return x >= 10.0 > 5 .`;

// Six muted colors for token highlighting. Chosen to be harmonious with the
// warm-gray + amber base, distinguishable from each other at a glance, and
// calm enough not to feel busy when many tokens are highlighted on one page.
// Each entry is { bg, text } for light mode and { dark, darkText } for dark.
export const TOKEN_PALETTE = [
  // Sage — cool muted green
  { bg: '#dde7df', text: '#3d5a47', dark: '#2a3d2f', darkText: '#bdd4c2' },
  // Slate blue — muted cool blue
  { bg: '#dde3ee', text: '#384a6b', dark: '#1f2c44', darkText: '#b6c2d8' },
  // Dusty rose — warm muted red-pink
  { bg: '#ecd6db', text: '#7a3e4c', dark: '#42252c', darkText: '#dcbcc4' },
  // Lavender — neutral purple-gray
  { bg: '#e3dcec', text: '#4d3e6b', dark: '#2b2440', darkText: '#c6bcd8' },
  // Teal — muted blue-green
  { bg: '#d2e1de', text: '#345b56', dark: '#1e3431', darkText: '#b3cfca' },
  // Plum — muted dark pink
  { bg: '#e5d2dc', text: '#5e3149', dark: '#3a1f2c', darkText: '#cfb3c1' },
];

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

export function initTheme() {
  const btn = document.getElementById('theme-toggle');
  btn.addEventListener('click', () => {
    const html = document.documentElement;
    const dark = html.classList.toggle('dark');
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  });
}

export function isDark() {
  return document.documentElement.classList.contains('dark');
}

// ---------------------------------------------------------------------------
// Tab navigation
// ---------------------------------------------------------------------------

let _tabHandlers = {};

export function initTabs() {
  const buttons = document.querySelectorAll('.tab-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => activateTab(btn.dataset.tab));
  });
  activateTab('tokens');
}

export function onTabActivated(tabName, handler) {
  _tabHandlers[tabName] = handler;
}

export function activateTab(name) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.dataset.active = btn.dataset.tab === name ? 'true' : 'false';
  });
  document.querySelectorAll('.tab-panel').forEach(panel => {
    panel.classList.toggle('hidden', panel.id !== `tab-${name}`);
  });
  if (_tabHandlers[name]) {
    _tabHandlers[name]();
  }
}

// ---------------------------------------------------------------------------
// Toasts
// ---------------------------------------------------------------------------

export function toast(message, kind = 'default', timeout = 3000) {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${kind === 'success' ? 'success' : kind === 'error' ? 'error' : ''}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => {
    el.style.transition = 'opacity 0.2s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 200);
  }, timeout);
}

// ---------------------------------------------------------------------------
// Build status pill
// ---------------------------------------------------------------------------

export function setBuildStatus(state, text) {
  const pill = document.getElementById('build-status');
  pill.classList.remove('hidden');
  pill.querySelectorAll('span').forEach((span, i) => {
    if (i === 0) {
      span.className = 'w-1.5 h-1.5 rounded-full ' + (
        state === 'ok' ? 'bg-emerald-500' :
        state === 'building' ? 'bg-amber-500 animate-pulse' :
        state === 'error' ? 'bg-red-500' :
        'bg-stone-400'
      );
    } else {
      span.textContent = text;
    }
  });
}

// ---------------------------------------------------------------------------
// Token color assignment (stable per token name)
// ---------------------------------------------------------------------------

const _colorMap = new Map();
export function colorFor(tokenName) {
  if (!_colorMap.has(tokenName)) {
    _colorMap.set(tokenName, TOKEN_PALETTE[_colorMap.size % TOKEN_PALETTE.length]);
  }
  return _colorMap.get(tokenName);
}

// ---------------------------------------------------------------------------
// Source highlighting helper
// ---------------------------------------------------------------------------

/**
 * Build HTML showing `source` with each token wrapped in a colored span.
 * tokens: [{lexeme, token, line, col}]
 * Optionally show a cursor at character index `cursorPos`.
 */
export function highlightSource(source, tokens, { cursorPos = null } = {}) {
  // Compute source-index spans by re-walking past whitespace
  const spans = [];
  let srcPos = 0;
  for (const tk of tokens) {
    while (srcPos < source.length && /[\s]/.test(source[srcPos])) srcPos++;
    spans.push({ start: srcPos, end: srcPos + tk.lexeme.length, name: tk.token });
    srcPos += tk.lexeme.length;
  }

  const dark = isDark();
  const parts = [];
  let i = 0;
  let spanIdx = 0;

  const cursorHtml = () => (
    '<span class="inline-block align-baseline" ' +
    'style="background:#ef4444;color:white;padding:0 3px;border-radius:2px;' +
    'animation:pulse 1s infinite;">▼</span>'
  );

  while (i < source.length) {
    if (cursorPos === i) parts.push(cursorHtml());
    if (spanIdx < spans.length && spans[spanIdx].start === i) {
      const { start, end, name } = spans[spanIdx];
      const c = colorFor(name);
      const bg = dark ? c.dark : c.bg;
      const fg = dark ? c.darkText : c.text;
      const text = escapeHtml(source.slice(start, end));
      parts.push(
        `<span class="token-span" style="background:${bg};color:${fg};" title="${escapeHtml(name)}">${text}</span>`
      );
      i = end;
      spanIdx++;
    } else {
      const ch = source[i];
      if (ch === '\n') parts.push('<br>');
      else if (ch === ' ') parts.push('&nbsp;');
      else if (ch === '\t') parts.push('&nbsp;&nbsp;&nbsp;&nbsp;');
      else parts.push(escapeHtml(ch));
      i++;
    }
  }
  if (cursorPos !== null && cursorPos >= source.length) parts.push(cursorHtml());

  return parts.join('');
}

export function tokenLegend(tokens) {
  const seen = new Set();
  const dark = isDark();
  const items = [];
  for (const tk of tokens) {
    if (seen.has(tk.token)) continue;
    seen.add(tk.token);
    const c = colorFor(tk.token);
    const bg = dark ? c.dark : c.bg;
    const fg = dark ? c.darkText : c.text;
    items.push(
      `<span class="inline-block px-2 py-0.5 rounded text-[11px] font-mono mr-1.5 mb-1" style="background:${bg};color:${fg};">${escapeHtml(tk.token)}</span>`
    );
  }
  return items.join('');
}

export function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
