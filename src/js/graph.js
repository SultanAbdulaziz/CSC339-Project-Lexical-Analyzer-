/**
 * Graph rendering — DOT → SVG via @viz-js/viz (Graphviz WASM),
 * with pan/zoom via svg-pan-zoom.
 */

const _panzoom = new WeakMap();
let _vizPromise = null;

function getViz() {
  if (typeof Viz === 'undefined' || typeof Viz.instance !== 'function') {
    throw new Error(
      'Viz.js did not load — check the browser console for a network/CSP error ' +
      'blocking https://cdn.jsdelivr.net/npm/@viz-js/viz/'
    );
  }
  if (!_vizPromise) _vizPromise = Viz.instance();
  return _vizPromise;
}

/**
 * Render `dotSource` into `containerEl`.
 * Sets up pan/zoom automatically. Call resetGraph() before re-rendering.
 */
export async function renderDot(containerEl, dotSource, opts = {}) {
  const { panZoom = true } = opts;

  // Destroy any existing pan/zoom instance
  _destroyPanzoom(containerEl);
  containerEl.innerHTML = '';

  // Load Viz.js (waits for WASM the first time, instant after)
  let viz;
  try {
    viz = await getViz();
  } catch (err) {
    _showError(containerEl, 'Graph engine failed to load', err.message);
    throw err;
  }

  // Render DOT → SVG element
  let svg;
  try {
    svg = viz.renderSVGElement(dotSource);
  } catch (err) {
    _showError(containerEl, 'DOT failed to render', err.message);
    throw err;
  }

  // ── Fix for container overflow ──────────
  // Make the SVG absolute *before* appending so it doesn't stretch the page layout.
  // We'll let svg-pan-zoom handle the sizing/viewport.
  svg.style.position = 'absolute';
  svg.style.top = '0';
  svg.style.left = '0';
  
  containerEl.appendChild(svg);

  // svg-pan-zoom needs explicit pixel dimensions, not "100%"
  const w = containerEl.clientWidth || 800;
  const h = containerEl.clientHeight || 520;
  svg.setAttribute('width', w);
  svg.setAttribute('height', h);
  svg.style.display = 'block';

  if (panZoom && typeof svgPanZoom === 'function') {
    try {
      const instance = svgPanZoom(svg, {
        zoomEnabled: true,
        controlIconsEnabled: false,
        fit: false,     // Don't squish the whole graph into view
        center: false,  // Don't center the whole graph
        minZoom: 0.05,
        maxZoom: 30,
        zoomScaleSensitivity: 0.3,
        dblClickZoomEnabled: false,
      });

      // Function to align the view to the start node (left side)
      const resetView = () => {
        const sizes = instance.getSizes();
        
        // Calculate the base scale (initial scale computed by svg-pan-zoom)
        // Since realZoom = relativeZoom * baseScale:
        const baseScale = sizes.realZoom / instance.getZoom();
        
        // Zoom to actual size (absolute realZoom = 1.0)
        if (baseScale > 0) {
          instance.zoom(1.0 / baseScale);
        } else {
          instance.zoom(1.0);
        }

        // Pan to left edge, vertically centered.
        // The graph's native height is instance.getSizes().viewBox.height.
        // Since realZoom is exactly 1.0, viewBox units map 1:1 with CSS pixels.
        const yOffset = (sizes.height - sizes.viewBox.height) / 2;
        
        // Add a small 20px padding to the left
        instance.pan({ x: 20, y: yOffset });
      };

      // Set initial view
      resetView();

      // Double-click resets to start node view instead of fitting everything
      svg.addEventListener('dblclick', e => {
        e.preventDefault();
        resetView();
      });
      _panzoom.set(containerEl, instance);
    } catch (err) {
      // Non-fatal — graph is visible, just no interactivity
      console.warn('svg-pan-zoom init failed:', err);
    }
  } else if (panZoom && typeof svgPanZoom !== 'function') {
    console.warn(
      'svg-pan-zoom not found — check that ' +
      'https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.2/dist/svg-pan-zoom.min.js loaded'
    );
  }

  return svg;
}

export function resetGraph(containerEl) {
  _destroyPanzoom(containerEl);
  containerEl.innerHTML = '';
}

function _destroyPanzoom(containerEl) {
  const inst = _panzoom.get(containerEl);
  if (inst) { try { inst.destroy(); } catch (_) { } _panzoom.delete(containerEl); }
}

export function downloadSvg(containerEl, filename = 'graph.svg') {
  const svg = containerEl.querySelector('svg');
  if (!svg) return;
  const src = new XMLSerializer().serializeToString(svg);
  const blob = new Blob([src], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function _showError(containerEl, title, detail) {
  containerEl.innerHTML = `
    <div class="absolute inset-0 flex flex-col items-center justify-center text-center px-6">
      <div class="text-red-600 dark:text-red-400 font-medium text-sm mb-1">${title}</div>
      <div class="text-stone-500 dark:text-stone-400 text-xs font-mono max-w-md">${detail}</div>
    </div>`;
}