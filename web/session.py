"""Run the terminal game unmodified, with its stdin/stdout wired to queues.

game_v6.py is a blocking program: it calls input() from inside nested loops in
combat, item selection and the radio dialogue. Rather than rewrite that control
flow, we run main() on a background thread and swap the two things it talks to —
builtins.input and sys.stdout — for queue-backed stand-ins. The game does not
know the difference, and game_v6.py stays untouched.
"""

import builtins
import queue
import sys
import threading
import time
import traceback

import game_v6
import runtime


# The real stdout, captured before any redirection, so the server can still
# print its startup banner while a session owns sys.stdout.
CONSOLE = sys.stdout

# Pushed onto the input queue to unblock a game thread that is waiting on a
# command we are never going to send (session reset, shutdown).
_ABANDON = object()


class _QueueWriter:
    """Minimal file-like object that forwards writes to a queue."""

    def __init__(self, out_q):
        self._out_q = out_q

    def write(self, text):
        if text:
            self._out_q.put(text)
        return len(text)

    def flush(self):
        pass

    def isatty(self):
        return False


class GameSession:
    """One playthrough, running on its own thread."""

    def __init__(self):
        self.input_q = queue.Queue()
        self.output_q = queue.Queue()
        self.finished = False
        self.awaiting_input = threading.Event()
        # Everything the session has emitted, so a phone that reloads the page
        # can pick the run back up where it left off.
        self.transcript = []
        self._thread = None
        self._writer = None
        self._real_input = None
        self._real_time = None

    # ── lifecycle ──────────────────────────────────────────

    def start(self):
        self._writer = _QueueWriter(self.output_q)
        self._real_input = builtins.input
        self._real_time = game_v6.time

        sys.stdout = self._writer
        builtins.input = self._web_input
        runtime.disable_typewriter_delay()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Abandon this session and hand the process back its own stdio."""
        self.finished = True
        self.input_q.put(_ABANDON)
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._restore()

    def _restore(self):
        # A newer session may already own these; only take back what is ours.
        if sys.stdout is self._writer:
            sys.stdout = CONSOLE
        if builtins.input is self._web_input and self._real_input is not None:
            builtins.input = self._real_input
        if isinstance(game_v6.time, runtime.NoSleep) and self._real_time is not None:
            game_v6.time = self._real_time

    def _run(self):
        try:
            game_v6.main()
        except SystemExit:
            # The game exits this way on quit and on every ending.
            pass
        except BaseException:
            self.output_q.put("\n\n[the mansion glitches]\n\n")
            self.output_q.put(traceback.format_exc())
        finally:
            self.finished = True
            self.awaiting_input.clear()
            self.output_q.put("\n\n── session over ── tap RESTART to begin again ──\n")
            self._restore()

    # ── the two ends of the pipe ───────────────────────────

    def _web_input(self, prompt=''):
        if prompt:
            self.output_q.put(prompt)
        self.awaiting_input.set()
        try:
            line = self.input_q.get()
        finally:
            self.awaiting_input.clear()
        if line is _ABANDON:
            raise EOFError
        # No echo here — the page echoes what you typed, in every build.
        return line

    def send_input(self, text):
        if not self.finished:
            self.input_q.put(text)

    def read_output(self, timeout=25.0):
        """Block for the next output, then drain whatever follows it.

        A single command usually produces a burst of prints. Waiting a beat
        after the first one lets the whole burst land in one response instead
        of dribbling out over several polls.
        """
        chunks = []
        try:
            chunks.append(self.output_q.get(timeout=timeout))
        except queue.Empty:
            return ''

        settle_until = time.monotonic() + 0.25
        while time.monotonic() < settle_until:
            try:
                chunks.append(self.output_q.get(timeout=0.05))
            except queue.Empty:
                break

        text = ''.join(chunks)
        self.transcript.append(text)
        return text

    def full_transcript(self):
        return ''.join(self.transcript)
