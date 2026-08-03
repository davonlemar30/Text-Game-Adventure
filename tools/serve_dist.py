#!/usr/bin/env python3
"""Serve dist/ with the headers SharedArrayBuffer needs.

    python3 tools/serve_dist.py

http.server does not send COOP/COEP, so the browser build cannot work behind
it — no cross-origin isolation means no SharedArrayBuffer means no blocking
stdin. This adds them, and matches what Cloudflare Pages sends via _headers.
"""

import os
import socket
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST, **kwargs)

    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


def lan_address():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('8.8.8.8', 80))
        return sock.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        sock.close()


def main():
    if not os.path.isdir(DIST):
        sys.exit('dist/ not found — run: python3 tools/build_browser.py')

    port = int(os.environ.get('PORT', '8001'))
    httpd = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    print(
        f'\n  browser build, cross-origin isolated\n'
        f'\n    this machine   http://localhost:{port}'
        f'\n    same Wi-Fi     http://{lan_address()}:{port}\n'
        f'\n  Ctrl-C to stop.\n',
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.server_close()


if __name__ == '__main__':
    main()
