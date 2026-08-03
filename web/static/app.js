'use strict';

const logEl     = document.getElementById('log');
const chipsEl   = document.getElementById('chips');
const formEl    = document.getElementById('entry');
const cmdEl     = document.getElementById('cmd');
const restartEl = document.getElementById('restart');

let transcript = '';
let lastChunk  = '';
let done       = false;
let polling    = false;
let backoff    = 500;

/* ── transcript rendering ─────────────────────────────────
   Prose wraps. Art — the mansion map, HP bars, separators —
   must keep its columns, so consecutive art lines are grouped
   into one block that scrolls sideways on its own.          */

const ART = /[█░─│★■·]/;

function isArt(line) {
  if (ART.test(line)) return true;
  return line.trim() !== '' && /^[\s|]+$/.test(line);
}

function render() {
  const atBottom = logEl.scrollHeight - logEl.scrollTop - logEl.clientHeight < 60;

  // Group consecutive lines by whether they are art. An art group becomes a
  // block that scrolls sideways; a prose group is a plain wrapping text node.
  const groups = [];
  transcript.split('\n').forEach((line) => {
    const art = isArt(line);
    const last = groups[groups.length - 1];
    if (last && last.art === art) last.lines.push(line);
    else groups.push({ art: art, lines: [line] });
  });

  const frag = document.createDocumentFragment();
  groups.forEach((group) => {
    const text = group.lines.join('\n');
    if (group.art) {
      const span = document.createElement('span');
      span.className = 'fixed';
      span.textContent = text;
      frag.appendChild(span);
    } else {
      frag.appendChild(document.createTextNode(text));
    }
  });

  logEl.replaceChildren(frag);
  if (atBottom) logEl.scrollTop = logEl.scrollHeight;
}

/* ── quick actions ───────────────────────────────────────
   Whatever the game just asked for is what the chips offer:
   numbered choices during combat, item menus and dialogue;
   movement and inspection while exploring.                 */

const NAV = [
  ['N', 'go north'], ['S', 'go south'], ['E', 'go east'], ['W', 'go west'],
  ['LOOK', 'look'], ['MAP', 'map'], ['NOTES', 'notes'],
  ['INV', 'inventory'], ['HINT', 'hint'], ['HELP', 'help'],
];

function parseMenu(chunk) {
  const found = new Map();
  const re = /\[(\d+)\]\s*([^\n]*)/g;
  let m;
  while ((m = re.exec(chunk)) !== null) {
    let label = m[2].split('|')[0].split('—')[0].replace(/\s+/g, ' ').trim();
    if (label.length > 12) label = label.slice(0, 12).trim();
    found.set(m[1], label ? m[1] + ' ' + label : m[1]);
  }
  return [...found.entries()].map(([key, label]) => [label, key]);
}

function chip(label, onClick, wide) {
  const b = document.createElement('button');
  b.type = 'button';
  b.textContent = label;
  if (wide) b.className = 'wide';
  b.addEventListener('click', onClick);
  return b;
}

function setChips(pairs, wide) {
  chipsEl.replaceChildren(
    ...pairs.map(([label, command]) => chip(label, () => send(command), wide))
  );
}

function updateChips() {
  if (done) {
    chipsEl.replaceChildren(chip('RESTART', restart, true));
    return;
  }
  if (/press enter/i.test(lastChunk)) {
    setChips([['CONTINUE', '']], true);
    return;
  }
  const menu = parseMenu(lastChunk);
  setChips(menu.length ? menu : NAV);
}

/* ── talking to the server ───────────────────────────────*/

function send(text) {
  if (done) return;
  cmdEl.value = '';
  fetch('/input', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: text }),
  }).catch(() => {});
}

function apply(data) {
  if (data.text) {
    transcript += data.text;
    lastChunk = data.text;
    render();
  }
  if (data.done && !done) {
    done = true;
    document.body.classList.add('done');
    cmdEl.blur();
    cmdEl.disabled = true;
  }
  updateChips();
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
    transcript = data.text || '';
    lastChunk = transcript.slice(-2000);
    done = false;
    document.body.classList.remove('done');
    cmdEl.disabled = false;
    render();
    logEl.scrollTop = logEl.scrollHeight;
    if (data.done) {
      done = true;
      document.body.classList.add('done');
      cmdEl.disabled = true;
    }
    updateChips();
  } catch (err) {
    /* server not up yet; the poll loop will retry */
  }
  poll();
}

async function restart() {
  await fetch('/reset', { method: 'POST' }).catch(() => {});
  transcript = '';
  lastChunk = '';
  done = false;
  document.body.classList.remove('done');
  cmdEl.disabled = false;
  render();
  restore();
}

/* ── wiring ──────────────────────────────────────────────*/

formEl.addEventListener('submit', (e) => {
  e.preventDefault();
  send(cmdEl.value.trim());
});

restartEl.addEventListener('click', restart);

document.addEventListener('visibilitychange', () => {
  if (!document.hidden) restore();
});

/* Keep the input bar above the on-screen keyboard. */
if (window.visualViewport) {
  const fit = () => {
    document.body.style.height = window.visualViewport.height + 'px';
    logEl.scrollTop = logEl.scrollHeight;
  };
  window.visualViewport.addEventListener('resize', fit);
  window.visualViewport.addEventListener('scroll', fit);
}

restore();
