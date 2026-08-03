'use strict';

/* HTTP transport for the local-network build. The UI lives in terminal.js. */

let done    = false;
let polling = false;
let backoff = 500;

Terminal.onCommand((text) => {
  fetch('/input', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: text }),
  }).catch(() => {});
});

Terminal.onRestart(async () => {
  await fetch('/reset', { method: 'POST' }).catch(() => {});
  Terminal.reset();
  done = false;
  restore();
});

function apply(data) {
  Terminal.append(data.text);
  if (data.done && !done) {
    done = true;
    Terminal.setDone(true);
  }
}

async function poll() {
  if (polling) return;
  polling = true;
  try {
    while (!done) {
      if (document.hidden) break;   // iOS drops long-polls in the background
      const res = await fetch('/poll');
      if (!res.ok) throw new Error('poll failed');
      apply(await res.json());
      backoff = 500;
    }
  } catch (err) {
    await new Promise(r => setTimeout(r, backoff));
    backoff = Math.min(backoff * 2, 8000);
  } finally {
    polling = false;
  }
  if (!done && !document.hidden) poll();
}

async function restore() {
  try {
    const res = await fetch('/state');
    const data = await res.json();
    done = !!data.done;
    Terminal.setTranscript(data.text || '');
    Terminal.setDone(done);
  } catch (err) {
    /* server not up yet; the poll loop will retry */
  }
  poll();
}

document.addEventListener('visibilitychange', () => {
  if (!document.hidden) restore();
});

restore();
