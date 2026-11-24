# dice-web

Static browser playground for the `dice` language. The site runs the runtime in a Pyodide web worker and renders charts with plain browser UI primitives instead of Matplotlib.

## Repo shape

- `dice/`
  Git submodule with the source runtime.
- `webbridge.py`
  Repo-local adapter exposing the stable browser-facing API over the vendored runtime.
- `runtime/`
  Copied browser runtime files served statically by the site.
- `src/`
  Browser app and worker.
- `styles/`
  Site styles.
- `vendor/`
  Self-hosted third-party browser dependencies (see below).

## Local run

1. Sync the browser runtime:

   ```bash
   ./scripts/sync-runtime.sh
   ```

2. Serve the repo root as a static site:

   ```bash
   python -m http.server 8000
   ```

3. Open [http://localhost:8000](http://localhost:8000).

## Current v1 surface

- Ace-based editor
- Pyodide runtime in a dedicated worker
- Structured JSON evaluation payloads through the repo-local `webbridge.py`
- Bar, line, and heatmap rendering in the browser
- Bundled example picker with ordered basic, D&D, and Python-extension examples
- Shareable URL state
- Local saved snippets

## Runtime sync

The worker loads only the copied browser runtime from `runtime/`. Re-run `./scripts/sync-runtime.sh` after changing either the vendored `dice` runtime files, the repo-local `webbridge.py`, or the bundled examples, then commit the refreshed `runtime/` directory with those changes.

## Self-hosted dependencies

The site makes no requests to third-party servers: every font, script, wasm
file and Python runtime file is served from this repository. Loading Google
Fonts or a CDN from the visitor's browser sends their IP address to that third
party, which German courts treat as a privacy violation without consent
(LG München I, 20.01.2022, 3 O 17493/20, on Google Fonts). Self-hosting
everything keeps the site free of that transfer and of a consent banner.
`tests/frontend/e2e/no-third-party.spec.js` runs the real app and fails on any
request to a host other than the local server. There is deliberately no CDN
fallback anywhere.

| Path | What | Version | Source | Licence |
|---|---|---|---|---|
| `vendor/fonts/` | IBM Plex Sans (variable, 400-600) and IBM Plex Mono (400, 500), latin subset, WOFF2 | Google Fonts v23 | `fonts.gstatic.com` files that the Google Fonts CSS API served | SIL OFL 1.1 (`OFL.txt`) |
| `vendor/ace/` | `ace.js`, `ext-language_tools.js`, `theme-tomorrow_night_bright.js` | 1.32.6 | npm `ace-builds`, `src-min/` | BSD-3-Clause (`LICENSE`) |
| `vendor/pyodide/` | `pyodide.js`, `pyodide.asm.js`, `pyodide.asm.wasm`, `python_stdlib.zip`, `pyodide-lock.json` | 0.26.4 | npm `pyodide` (byte-identical to the jsDelivr `full/` files) | MPL-2.0 (`LICENSE`); the Python stdlib is under the PSF licence |
| `vendor/d3.min.js`, `vendor/observable-plot.umd.min.js` | charts | d3 7.9.0, Plot 0.6.17 | npm | ISC |

Only the files the page actually loads are vendored. Ace loads its theme from
the folder `ace.js` was loaded from. The app loads no Pyodide packages (the
runtime is pure Python stdlib), so no package wheels are vendored and
`pyodide.mjs` is left out because the worker uses `importScripts`.

GitHub Pages serves the repo root of `main` as-is (`.nojekyll`), so the
committed `vendor/` files are deployed without a build step. The largest file
is `pyodide.asm.wasm` at about 10 MB, well under the Pages limits of 100 MiB
per file and 1 GB per site.

### Updating a vendored dependency

Run these in a scratch directory outside the repo, then copy the files over.

- **Pyodide:** `npm pack pyodide@<version>` and unpack it; copy the five files
  listed above into `vendor/pyodide/`; fetch `LICENSE` from the pyodide
  repository at the same tag. The version is fixed by the files themselves:
  `loadPyodide` refuses an `indexURL` whose files have a different version.
  If the app starts loading Pyodide packages (`loadPackage`, `micropip`),
  vendor those wheels too; the no-third-party test catches anything missed.
- **Ace:** `npm pack ace-builds@<version>`; copy `ace.js`,
  `ext-language_tools.js` and every theme, mode or extension the page uses
  from `src-min/` into `vendor/ace/`, and `LICENSE`.
- **Fonts:** request the Google Fonts CSS URL for the families and weights
  with a current browser User-Agent, download the `latin` subset WOFF2 files
  it lists, and update `vendor/fonts/fonts.css` (file names and
  `unicode-range`).

Afterwards run `npm run test:frontend`; the no-third-party test opens the
real app, boots Pyodide and runs a program.
