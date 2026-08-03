"""Serve the mansion over HTTP so it can be played from a phone.

    python3 -m web.server

Then open the printed LAN address on your iPhone, on the same Wi-Fi.
Standard library only — no dependencies, no build step.
"""

import json
import mimetypes
import os
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import runtime  # noqa: E402
from web.session import CONSOLE, GameSession  # noqa: E402

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
POLL_TIMEOUT = 25.0

_session = None
_session_lock = threading.Lock()


def get_session():
    global _session
    with _session_lock:
        if _session is None:
            _session = GameSession()
            _session.start()
        return _session


def reset_session():
    global _session
    with _session_lock:
        if _session is not None:
            _session.stop()
        runtime.clear_save()   # RESTART means start over, not resume
        _session = GameSession()
        _session.start()
        return _session


class Handler(BaseHTTPRequestHandler):
    server_version = 'MansionTerminal/1.0'

    def log_message(self, fmt, *args):
        # sys.stdout belongs to the game while a session is running.
        pass

    # ── helpers ────────────────────────────────────────────

    def _send(self, code, body, content_type='application/json; charset=utf-8'):
        if isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # Phone backgrounded the tab mid-poll. Expected; not an error.
            pass

    def _send_json(self, code, payload):
        self._send(code, json.dumps(payload))

    def _send_static(self, filename):
        path = os.path.normpath(os.path.join(STATIC_DIR, filename))
        if not path.startswith(STATIC_DIR) or not os.path.isfile(path):
            self._send(404, 'not found', 'text/plain; charset=utf-8')
            return
        ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        if ctype.startswith('text/') or ctype in ('application/javascript', 'application/manifest+json'):
            ctype += '; charset=utf-8'
        with open(path, 'rb') as fh:
            self._send(200, fh.read(), ctype)

    def _read_json_body(self):
        try:
            length = int(self.headers.get('Content-Length') or 0)
        except ValueError:
            return {}
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return {}

    # ── routes ─────────────────────────────────────────────

    def do_GET(self):
        route = self.path.split('?', 1)[0]

        if route == '/':
            self._send_static('index.html')

        elif route.startswith('/static/'):
            self._send_static(route[len('/static/'):])

        elif route == '/state':
            session = get_session()
            self._send_json(200, {
                'text': session.full_transcript(),
                'awaiting': session.awaiting_input.is_set(),
                'done': session.finished,
            })

        elif route == '/poll':
            session = get_session()
            text = session.read_output(timeout=POLL_TIMEOUT)
            self._send_json(200, {
                'text': text,
                'awaiting': session.awaiting_input.is_set(),
                'done': session.finished,
            })

        else:
            self._send(404, 'not found', 'text/plain; charset=utf-8')

    def do_POST(self):
        route = self.path.split('?', 1)[0]

        if route == '/input':
            session = get_session()
            session.send_input(str(self._read_json_body().get('text', '')))
            self._send_json(200, {'ok': True})

        elif route == '/reset':
            reset_session()
            self._send_json(200, {'ok': True})

        else:
            self._send(404, 'not found', 'text/plain; charset=utf-8')


def lan_address():
    """Best guess at the address a phone on the same Wi-Fi should open."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No packets are sent; this just picks the outbound interface.
        sock.connect(('8.8.8.8', 80))
        return sock.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        sock.close()


def main():
    port = int(os.environ.get('PORT', '8000'))
    httpd = ThreadingHTTPServer(('0.0.0.0', port), Handler)

    banner = (
        "\n"
        "  ZOMBIE APOCALYPSE: THE MANSION — web terminal\n"
        "\n"
        f"    this machine   http://localhost:{port}\n"
        f"    your iPhone    http://{lan_address()}:{port}\n"
        "\n"
        "  Same Wi-Fi. Ctrl-C to stop.\n"
    )
    print(banner, file=CONSOLE, flush=True)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  the mansion goes quiet.\n", file=CONSOLE, flush=True)
    finally:
        httpd.server_close()


if __name__ == '__main__':
    main()
