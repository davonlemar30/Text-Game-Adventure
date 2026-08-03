/* Runs the game inside Pyodide.
 *
 * The game calls input() from inside nested loops, which only works if stdin
 * can block. It can here: this is a worker, so it may call Atomics.wait on a
 * SharedArrayBuffer that the page writes commands into. That is why the page
 * needs COOP/COEP — without cross-origin isolation there is no
 * SharedArrayBuffer and no blocking stdin.
 */

import { loadPyodide } from '/pyodide/pyodide.mjs';

let stdinCtrl  = null;   // Int32Array(1): 0 = nothing pending, else byteLength + 1
let stdinBytes = null;   // Uint8Array: the UTF-8 command
let saved      = '';     // latest save blob, mirrored from the page

const decoder = new TextDecoder('utf-8');
const outDecoder = new TextDecoder('utf-8');

function readStdin() {
  // Loop rather than wait forever, so a terminated worker is not wedged.
  for (;;) {
    if (Atomics.load(stdinCtrl, 0) !== 0) break;
    Atomics.wait(stdinCtrl, 0, 0, 200);
  }
  const packed = Atomics.exchange(stdinCtrl, 0, 0);
  if (packed < 0) return null;                      // shutdown -> EOF
  // TextDecoder refuses views backed by shared memory, so copy out first.
  return decoder.decode(new Uint8Array(stdinBytes.subarray(0, packed - 1)));
}

function writeStdout(buffer) {
  // Raw writes, not line-batched: input()'s prompt has no trailing newline and
  // must reach the screen before the game blocks waiting for an answer.
  const text = outDecoder.decode(buffer, { stream: true });
  if (text) self.postMessage({ type: 'out', text });
  return buffer.length;
}

async function boot(sab, initialSave) {
  stdinCtrl  = new Int32Array(sab, 0, 1);
  stdinBytes = new Uint8Array(sab, 4);
  saved = initialSave || '';

  self.postMessage({ type: 'status', text: 'loading python…' });
  const pyodide = await loadPyodide({ indexURL: '/pyodide/' });

  self.postMessage({ type: 'status', text: 'loading the mansion…' });
  const manifest = await (await fetch('/game/manifest.json')).json();
  pyodide.FS.mkdir('/game');
  for (const name of manifest.files) {
    const source = await (await fetch('/game/' + name)).text();
    const path = '/game/' + name;
    const dir = path.slice(0, path.lastIndexOf('/'));
    if (dir !== '/game') {
      try { pyodide.FS.mkdir(dir); } catch (e) { /* already there */ }
    }
    pyodide.FS.writeFile(path, source);
  }

  // localStorage is main-thread only, so saves round-trip through the page.
  pyodide.registerJsModule('bridge', {
    save(text) {
      saved = text;
      self.postMessage({ type: 'save', text: text });
    },
    load() {
      return saved;
    },
  });

  pyodide.setStdout({ write: writeStdout });
  pyodide.setStderr({ write: writeStdout });
  pyodide.setStdin({ stdin: readStdin });

  self.postMessage({ type: 'ready' });

  const bootstrap = await (await fetch('/game/bootstrap.py')).text();
  await pyodide.runPythonAsync(bootstrap);

  self.postMessage({ type: 'done' });
}

self.onmessage = (event) => {
  const msg = event.data;
  if (msg.type === 'boot') {
    boot(msg.sab, msg.save).catch((err) => {
      self.postMessage({ type: 'out', text: '\n\n[the mansion glitches]\n\n' + err + '\n' });
      self.postMessage({ type: 'done' });
    });
  }
};
