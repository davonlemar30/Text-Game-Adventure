'use strict';

/* The terminal UI, with no opinion about where the game runs.
   web/static/app.js drives it over HTTP; browser/app.js drives it from a
   Pyodide worker. Both get the same transcript, chips and keyboard handling. */

const Terminal = (function () {

  const logEl     = document.getElementById('log');
  const chipsEl   = document.getElementById('chips');
  const formEl    = document.getElementById('entry');
  const cmdEl     = document.getElementById('cmd');
  const restartEl = document.getElementById('restart');
  const statusEl  = document.getElementById('status');

  let transcript = '';
  let pending    = '';
  let frame      = 0;
  // Chips describe the question the game is asking *now*, so menu detection
  // only ever looks at output produced since the last command was sent.
  let anchor     = 0;
  let done       = false;
  let commandCb  = null;
  let restartCb  = null;

  /* ── rendering ───────────────────────────────────────────
     Prose wraps. Art — the mansion map, HP bars, separators —
     must keep its columns, so consecutive art lines are grouped
     into one block that scrolls sideways on its own.          */

  const ART = /[█░─│★■·]/;

  function isArt(line) {
    if (ART.test(line)) return true;
    return line.trim() !== '' && /^[\s|]+$/.test(line);
  }

  function flush(extra) {
    transcript += pending + (extra || '');
    pending = '';
    render();
    updateChips();
  }

  function render() {
    const atBottom = logEl.scrollHeight - logEl.scrollTop - logEl.clientHeight < 60;

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
      ...pairs.map(([label, command]) => chip(label, () => submit(command), wide))
    );
  }

  function updateChips() {
    if (done) {
      chipsEl.replaceChildren(chip('RESTART', () => restartCb && restartCb(), true));
      return;
    }
    const recent = transcript.slice(anchor);
    if (/press enter/i.test(recent)) {
      setChips([['CONTINUE', '']], true);
      return;
    }
    const menu = parseMenu(recent);
    setChips(menu.length ? menu : NAV);
  }

  /* ── input ───────────────────────────────────────────────*/

  function submit(text) {
    if (done || !commandCb) return;
    cmdEl.value = '';
    // Echo locally so the transcript reads like a terminal in every build,
    // and so the next menu is measured from here.
    flush(text + '\n');
    anchor = transcript.length;
    commandCb(text);
  }

  formEl.addEventListener('submit', (e) => {
    e.preventDefault();
    submit(cmdEl.value.trim());
  });

  restartEl.addEventListener('click', () => restartCb && restartCb());

  /* Keep the input bar above the on-screen keyboard. */
  if (window.visualViewport) {
    const fit = () => {
      document.body.style.height = window.visualViewport.height + 'px';
      logEl.scrollTop = logEl.scrollHeight;
    };
    window.visualViewport.addEventListener('resize', fit);
    window.visualViewport.addEventListener('scroll', fit);
  }

  /* ── public surface ──────────────────────────────────────*/

  return {
    /* Output can arrive one write at a time, so coalesce to a frame before
       touching the DOM. It keeps rendering cheap and lets chip detection see
       a whole burst rather than its last fragment. */
    append(text) {
      if (!text) return;
      pending += text;
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        flush('');
      });
    },

    setTranscript(text) {
      transcript = text || '';
      pending = '';
      anchor = Math.max(0, transcript.length - 2000);
      render();
      logEl.scrollTop = logEl.scrollHeight;
      updateChips();
    },

    reset() {
      transcript = '';
      pending = '';
      anchor = 0;
      this.setDone(false);
      render();
      updateChips();
    },

    setDone(flag) {
      done = !!flag;
      document.body.classList.toggle('done', done);
      cmdEl.disabled = done;
      if (done) cmdEl.blur();
      updateChips();
    },

    status(text) {
      if (statusEl) statusEl.textContent = text || '';
    },

    onCommand(cb) { commandCb = cb; },
    onRestart(cb) { restartCb = cb; },
  };
})();
