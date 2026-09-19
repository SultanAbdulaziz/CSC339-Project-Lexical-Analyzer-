# Development and Testing

## Requirements

- Python 3.10 or later for local tests and a simple HTTP server
- A current browser with WebAssembly support
- Internet access on first load for the CDN-hosted browser dependencies
- Python 3.11 or later and Manim only when regenerating documentation animations

The application itself does not need a Python package installation because Python runs inside Pyodide in the browser.

## Run the application

```powershell
python -m http.server 8000 --directory src
```

Use a local HTTP server instead of opening the HTML file directly.

## Run the regression suite

```powershell
python -m unittest discover -s tests -v
```

The current suite checks:

1. operator precedence and postfix conversion,
2. Kleene star, positive closure, and optional construction,
3. equal-length token priority,
4. longest-match tokenization,
5. line and column tracking,
6. invalid-character reporting,
7. NFA and DFA DOT generation,
8. consistency between the stepper and full scan.

Tests import the same files shipped to Pyodide. This prevents the browser version and test version from silently diverging.

## Change the Python core

The recommended order is:

1. Add or update a regression test.
2. Change the implementation in `src/lib`.
3. Run the Python tests.
4. Serve `src` locally and complete a browser smoke test.
5. Check Scan, NFA, DFA, and Step-by-Step after rebuilding the default rules.

Keep `lex_bridge.py` focused on serialization, visualization data, and stepper state. Core automata behavior belongs in `regex_to_NFA.py` or `NFA_to_DFA.py`.

## Regenerate the Manim assets

Animation source is stored in `docs/animations/lexical_analyzer.py`. Install the documentation dependency in an isolated environment, then run:

```powershell
python -m venv .manim-venv
.\.manim-venv\Scripts\Activate.ps1
python -m pip install -r docs\animations\requirements.txt
python docs\animations\render.py
```

The render helper creates these files:

- `docs/assets/thompson-construction.gif`
- `docs/assets/subset-construction.gif`
- `docs/assets/maximal-munch.gif`

Generated assets are committed so README and Wiki visitors do not need Manim.

## Documentation workflow

The Markdown files in `docs/wiki` are the reviewable source for the GitHub Wiki. Keeping them in the main repository allows documentation changes to be tested and reviewed with the code before they are copied to the separate Wiki repository.

Before publishing documentation:

- verify every relative asset path,
- confirm that commands work from a fresh clone,
- avoid claiming features that are not implemented,
- keep complexity statements tied to this implementation,
- regenerate animations when their explanation changes.

## Prepare a GitHub Pages release

The workflow in `.github/workflows/pages.yml` uploads `src` as a static Pages artifact only when it is started manually. A normal push to `UI` does not deploy the site, and no build command is required.

Before the first release:

1. Finalize the repository name and public address.
2. Review the complete diff and run the test suite.
3. Commit and push the tested changes to `UI`.
4. Open the repository's **Settings -> Pages** section.
5. Set the Pages source to **GitHub Actions**.
6. Open the **Actions** tab and manually run the Pages workflow.
7. Wait for the `github-pages` deployment to succeed.
8. Verify the public URL in a clean browser session.
9. Add the verified URL as the repository homepage and README demo link.

Do not advertise the URL before the workflow succeeds. A configured workflow and a deployed site are different states.

## Browser acceptance checklist

- The loading screen reaches a successful DFA build.
- Editing and reordering rules survives a refresh.
- `Ctrl/Cmd + Enter` builds and scans in the correct tabs.
- The sample program produces 76 tokens.
- NFA and DFA graphs render in light and dark themes.
- Step playback can start, pause, change speed, finish, and reset.
- A narrow viewport keeps controls usable without covering the graph.
