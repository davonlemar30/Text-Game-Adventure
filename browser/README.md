# Browser build — the mansion with no server

Runs the whole game in the browser. Python itself is compiled to WebAssembly
(Pyodide), so there is no server, no laptop and no home network involved — just
a URL that works on a phone, on cellular, anywhere.

`game_v6.py` runs **unmodified**. It is the same file the terminal runs.

## Build and run locally

```bash
python3 tools/build_browser.py    # assembles dist/
python3 tools/serve_dist.py       # serves it with the right headers
```

Then open `http://localhost:8001`.

Do **not** use `python3 -m http.server` for this — see "Why the headers matter"
below. `serve_dist.py` exists precisely because http.server can't do it.

`--clean` wipes `dist/` first. The Pyodide runtime is cached in `.cache/` after
the first download, so rebuilds are instant.

## How it works

The game is a blocking program — it calls `input()` from inside nested loops in
combat, item selection and the radio dialogue. In a browser that normally can't
work, because JavaScript won't block. The way around it:

- Python runs in a **Web Worker**, not on the page.
- `worker.mjs` gives Pyodide a `stdin` function that blocks on
  `Atomics.wait` against a `SharedArrayBuffer`.
- When you submit a command, the page writes it into that shared buffer and
  notifies. The worker wakes up and `input()` returns.

Output goes the other way as raw writes rather than line batches, because
`input()`'s prompt has no trailing newline and has to reach the screen *before*
the game blocks waiting for an answer.

Saves live in the page's `localStorage`. `localStorage` is main-thread only, so
they round-trip through the worker bridge — `runtime.SAVE_HOOK` posts to the
page, and the page hands the blob back at boot.

The UI is the same `terminal.js` the local-network build uses. Only the
transport differs: `browser/app.js` talks to a worker, `web/static/app.js` talks
to HTTP.

## Why the headers matter

`SharedArrayBuffer` only exists on a **cross-origin isolated** page, which needs:

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

No isolation → no `SharedArrayBuffer` → no blocking stdin → no game. The page
checks `crossOriginIsolated` on load and says so plainly rather than failing
somewhere deep inside Pyodide.

`require-corp` also means every subresource must be same-origin or explicitly
opt in, which is why the Pyodide runtime is downloaded into `dist/pyodide/` at
build time instead of loaded from a CDN.

## Deploying to Cloudflare Pages

Cloudflare Pages sends those headers from the `_headers` file in `dist/`.

1. Cloudflare dashboard → Workers & Pages → Create → Pages → connect this repo
2. Build command: `python3 tools/build_browser.py`
3. Build output directory: `dist`
4. Framework preset: none

Every push gets a preview URL, which is the fastest way to test on a real phone.

**GitHub Pages will not work** without a hack. Pages cannot send response
headers, so it needs the `coi-serviceworker` shim to fake them — which has
reported iOS Safari problems. Cloudflare Pages sends the real thing.

## Numbers worth knowing

- The Pyodide runtime is ~13 MB on disk, ~6 MB over the wire compressed.
  It is cached by the browser after the first load.
- No Python packages are needed — the game is pure standard library.
- Pinned to Pyodide 314.0.3 in `tools/build_browser.py`.

## Known gaps

- No `apple-touch-icon`, so Add to Home Screen uses a screenshot rather than a
  proper icon.
- The transcript itself is not persisted across a reload — the *game* is, via
  autosave, so a reload offers to pick the run back up.
