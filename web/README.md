# Web terminal — playing the mansion on your phone

Runs the existing game over HTTP so you can play it on an iPhone.
Standard library only. No dependencies, no build step, no account.

## Run it

From the repo root, on the computer:

```bash
python3 -m web.server
```

It prints two addresses:

```
    this machine   http://localhost:8000
    your iPhone    http://192.168.x.x:8000
```

Open the second one on your phone. Same Wi-Fi, that's the only requirement.
Use `PORT=8080 python3 -m web.server` if 8000 is taken.

**Add to Home Screen** (Share → Add to Home Screen) launches it full-screen with
no browser chrome, which is how it's meant to be played.

## Playing

Type commands as usual, or use the chips above the keyboard:

- Exploring — `N S E W · LOOK · MAP · NOTES · INV · HINT · HELP`
- In combat, item menus, and dialogue — the numbered choices the game is
  currently offering, so a whole fight is playable by tapping
- `RESTART` (top right) abandons the run and starts a new one

## How it works

`game_v6.py` is **not modified**. It is a blocking program — it calls `input()`
from inside nested loops in combat, item selection and the radio dialogue — so
instead of rewriting that control flow, `session.py` runs `main()` on a
background thread and swaps out the two things it talks to:

- `builtins.input` → blocks on a queue the browser posts into
- `sys.stdout` → a writer that pushes into a queue the browser polls

`server.py` is a stdlib `ThreadingHTTPServer` over that:

| Route | |
|---|---|
| `GET /` , `/static/*` | the page |
| `GET /state` | full transcript so far — lets a reloaded phone rejoin the run |
| `GET /poll` | long-poll, up to 25s, returns the next burst of output |
| `POST /input` | send a command |
| `POST /reset` | abandon the session and start fresh |

`typewriter()`'s per-character sleep is disabled for web sessions — output
arrives a chunk at a time over HTTP either way, so the delay would just be dead
air. The atmosphere is carried by the page styling instead.

One session at a time: `sys.stdout` is process-global, so this serves one
player. That's the intended use — it's a development and playtesting tool.

## Limits

- **Local network only.** Do not expose this port to the internet; there is no
  authentication and it runs arbitrary game state for whoever connects.
- **One player at a time**, since `sys.stdout` is process-global.

## If you want to play without a computer on the network

Use the browser build instead — see `browser/README.md`. It runs the same game
entirely in the browser via Pyodide, so it needs no server at all and works from
a phone anywhere. This build stays useful for development, because it starts
instantly instead of loading ~6 MB of WebAssembly on every change.
