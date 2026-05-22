# CSC339-Project-Lexical-Analyzer

## How to Run Locally

Because this is a static web app that uses WebAssembly (Pyodide) to run Python in the browser, you must serve it using a local HTTP server.

1. Open a terminal or command prompt.
2. Navigate to the `src` directory of the project:
   ```bash
   cd src
   ```
3. Start a basic Python HTTP server:
   ```bash
   python -m http.server 8000
   ```
4. Open your web browser and go to: [http://localhost:8000](http://localhost:8000)

> **Note:** The first time you load the page, it may take a few seconds to download the Pyodide runtime. Subsequent reloads will be fast.
