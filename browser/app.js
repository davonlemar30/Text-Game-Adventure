'use strict';

/* Worker transport for the browser build. The UI lives in terminal.js. */

const SAVE_KEY = 'mansion.save.v1';
const STDIN_BYTES = 4096;

let worker = null;
let ctrl   = null;
let bytes  = null;

const encoder = new TextEncoder();

function fatal(message) {
  Terminal.status('');
  Terminal.setTranscript('\n  ' + message + '\n');
  Terminal.setDone(true);
}

function start() {
  if (!self.crossOriginIsolated) {
    fatal(
      'This page needs cross-origin isolation to run Python.\n\n' +
      '  The server must send:\n' +
      '    Cross-Origin-Opener-Policy: same-origin\n' +
      '    Cross-Origin-Embedder-Policy: require-corp\n\n' +
      '  Locally, use: python3 tools/serve_dist.py'
    );
    return;
  }

  const sab = new SharedArrayBuffer(4 + STDIN_BYTES);
  ctrl  = new Int32Array(sab, 0, 1);
  bytes = new Uint8Array(sab, 4);

  worker = new Worker('/static/worker.mjs', { type: 'module' });
  worker.onmessage = (event) => {
    const msg = event.data;
    if (msg.type === 'out')         Terminal.append(msg.text);
    else if (msg.type === 'status') Terminal.status(msg.text);
    else if (msg.type === 'ready')  Terminal.status('');
    else if (msg.type === 'save')   persist(msg.text);
    else if (msg.type === 'done')   Terminal.setDone(true);
  };
  worker.onerror = (err) => fatal('The worker failed to start: ' + err.message);

  worker.postMessage({ type: 'boot', sab: sab, save: load() });
}

function persist(text) {
  try {
    if (text) localStorage.setItem(SAVE_KEY, text);
    else localStorage.removeItem(SAVE_KEY);
  } catch (err) {
    /* private browsing, or storage full — the run just won't survive a reload */
  }
}

function load() {
  try {
    return localStorage.getItem(SAVE_KEY) || '';
  } catch (err) {
    return '';
  }
}

Terminal.onCommand((text) => {
  if (!ctrl) return;
  const encoded = encoder.encode(text).subarray(0, STDIN_BYTES - 1);
  bytes.set(encoded);
  Atomics.store(ctrl, 0, encoded.length + 1);
  Atomics.notify(ctrl, 0);
});

Terminal.onRestart(() => {
  persist('');
  if (worker) worker.terminate();
  Terminal.reset();
  Terminal.status('waking up…');
  start();
});

start();
