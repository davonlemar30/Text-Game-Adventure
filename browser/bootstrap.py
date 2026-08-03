"""Entry point inside Pyodide. Runs on the worker thread, not the page."""

import sys

sys.path.insert(0, '/game')

import bridge      # registered by worker.mjs  # noqa: E402
import runtime     # noqa: E402
import game_v6     # noqa: E402

# Saves live in the page's localStorage, reached through the worker bridge.
runtime.SAVE_HOOK = lambda text: bridge.save(text)
runtime.LOAD_HOOK = lambda: bridge.load()

runtime.disable_typewriter_delay()

try:
    game_v6.main()
except SystemExit:
    pass

print("\n\n── session over ── tap RESTART to begin again ──")
