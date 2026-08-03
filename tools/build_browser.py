#!/usr/bin/env python3
"""Assemble dist/ — the static site that runs the game in a browser.

    python3 tools/build_browser.py

Game sources are copied from the real files rather than kept as a second copy
in browser/, so the browser build can never drift from the terminal build.
Standard library only; the Pyodide runtime comes from the npm registry.
"""

import json
import os
import shutil
import sys
import tarfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')
CACHE = os.path.join(ROOT, '.cache')

PYODIDE_VERSION = '314.0.3'
PYODIDE_URL = (
    f'https://registry.npmjs.org/pyodide/-/pyodide-{PYODIDE_VERSION}.tgz'
)
# Everything the runtime needs and nothing else — no packages, the game is
# pure standard library.
PYODIDE_FILES = [
    'pyodide.mjs',
    'pyodide.asm.mjs',
    'pyodide.asm.wasm',
    'python_stdlib.zip',
    'pyodide-lock.json',
]

# Copied into dist/game/ and loaded into Pyodide's filesystem at boot.
GAME_FILES = [
    'game_v6.py',
    'rooms_loader.py',
    'runtime.py',
    'content/__init__.py',
    'content/rooms_data.py',
]

STATIC_FILES = [
    (os.path.join('web', 'static', 'style.css'), 'style.css'),
    (os.path.join('web', 'static', 'terminal.js'), 'terminal.js'),
    (os.path.join('web', 'static', 'manifest.webmanifest'), 'manifest.webmanifest'),
    (os.path.join('browser', 'app.js'), 'app.js'),
    (os.path.join('browser', 'worker.mjs'), 'worker.mjs'),
]


def log(message):
    print(f'  {message}', flush=True)


def fetch_pyodide():
    os.makedirs(CACHE, exist_ok=True)
    tarball = os.path.join(CACHE, f'pyodide-{PYODIDE_VERSION}.tgz')

    if not os.path.isfile(tarball):
        log(f'downloading pyodide {PYODIDE_VERSION}…')
        with urllib.request.urlopen(PYODIDE_URL, timeout=300) as response:
            with open(tarball, 'wb') as fh:
                shutil.copyfileobj(response, fh)
    else:
        log(f'pyodide {PYODIDE_VERSION} already cached')

    target = os.path.join(DIST, 'pyodide')
    os.makedirs(target, exist_ok=True)
    with tarfile.open(tarball) as tar:
        for name in PYODIDE_FILES:
            member = tar.getmember(f'package/{name}')
            member.name = name
            tar.extract(member, target, filter='data')
    log(f'pyodide runtime -> dist/pyodide/ ({len(PYODIDE_FILES)} files)')


def copy_game():
    target = os.path.join(DIST, 'game')
    os.makedirs(target, exist_ok=True)
    for relative in GAME_FILES:
        destination = os.path.join(target, relative)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, relative), destination)

    shutil.copy2(
        os.path.join(ROOT, 'browser', 'bootstrap.py'),
        os.path.join(target, 'bootstrap.py'),
    )

    with open(os.path.join(target, 'manifest.json'), 'w', encoding='utf-8') as fh:
        json.dump({'files': GAME_FILES}, fh)
    log(f'game sources -> dist/game/ ({len(GAME_FILES)} files)')


def copy_static():
    target = os.path.join(DIST, 'static')
    os.makedirs(target, exist_ok=True)
    for source, name in STATIC_FILES:
        shutil.copy2(os.path.join(ROOT, source), os.path.join(target, name))

    shutil.copy2(
        os.path.join(ROOT, 'browser', 'index.html'),
        os.path.join(DIST, 'index.html'),
    )
    shutil.copy2(
        os.path.join(ROOT, 'browser', '_headers'),
        os.path.join(DIST, '_headers'),
    )
    log(f'page -> dist/ ({len(STATIC_FILES) + 2} files)')


def main():
    if '--clean' in sys.argv and os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST, exist_ok=True)

    print('\nbuilding dist/\n')
    copy_game()
    copy_static()
    fetch_pyodide()
    print('\ndone. serve it with: python3 tools/serve_dist.py\n')


if __name__ == '__main__':
    main()
