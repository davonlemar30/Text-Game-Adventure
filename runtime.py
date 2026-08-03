"""Platform-neutral helpers shared by every way the game gets played.

The terminal build, the local web server and the browser build all run the same
game_v6.py. What differs is where output goes and where saves live — so that
part lives here, behind hooks the platform adapter sets.
"""

import json
import os
import time

SAVE_VERSION = 1

DEFAULT_SAVE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'savegame.json'
)

# Set by the platform adapter. save: callable(str) -> None. load: callable() -> str | None.
# Left as None, saves go to a JSON file next to the game; the browser build
# points these at localStorage instead.
SAVE_HOOK = None
LOAD_HOOK = None


class NoSleep:
    """Stand-in for the time module with sleep() disabled.

    typewriter() sleeps between characters, which is atmosphere in a terminal
    and dead air anywhere output is delivered a chunk at a time. Everything
    else on the module passes straight through.
    """

    def sleep(self, seconds):
        return None

    def __getattr__(self, name):
        return getattr(time, name)


def disable_typewriter_delay():
    import game_v6
    game_v6.time = NoSleep()


# ── snapshotting ───────────────────────────────────────────

def _snapshot_player(player):
    """Capture Player generically, so new attributes survive without edits here.

    Every attribute is JSON-able as-is except the sets (examined,
    visited_rooms), which are recorded by name so restore can rebuild them.
    """
    fields = {}
    sets = []
    for key, value in vars(player).items():
        if isinstance(value, set):
            sets.append(key)
            fields[key] = sorted(value)
        else:
            fields[key] = value
    return {'fields': fields, 'sets': sets}


def _restore_player(data):
    import game_v6
    player = game_v6.Player()
    set_keys = set(data.get('sets', []))
    for key, value in data.get('fields', {}).items():
        setattr(player, key, set(value) if key in set_keys else value)
    return player


def _snapshot_rooms(rooms):
    """Only items and objects mutate during play; everything else is rebuilt."""
    return {
        name: {
            'items': dict(room.get('items', {})),
            'objects': dict(room.get('objects', {})),
        }
        for name, room in rooms.items()
    }


def _restore_rooms(data):
    import game_v6
    rooms = game_v6.build_rooms()
    for name, state in data.items():
        if name in rooms:
            rooms[name]['items'] = dict(state.get('items', {}))
            rooms[name]['objects'] = dict(state.get('objects', {}))
    return rooms


def snapshot(player, rooms, current_room):
    return {
        'version': SAVE_VERSION,
        'current_room': current_room,
        'player': _snapshot_player(player),
        'rooms': _snapshot_rooms(rooms),
    }


def restore(data):
    version = data.get('version')
    if version != SAVE_VERSION:
        raise ValueError(
            f"save was written by a different version of the game "
            f"(found {version!r}, expected {SAVE_VERSION})"
        )
    return (
        _restore_player(data['player']),
        _restore_rooms(data.get('rooms', {})),
        data['current_room'],
    )


# ── persistence ────────────────────────────────────────────

def _write(text):
    if SAVE_HOOK is not None:
        SAVE_HOOK(text)
        return
    with open(DEFAULT_SAVE_PATH, 'w', encoding='utf-8') as fh:
        fh.write(text)


def _read():
    if LOAD_HOOK is not None:
        return LOAD_HOOK()
    if not os.path.isfile(DEFAULT_SAVE_PATH):
        return None
    with open(DEFAULT_SAVE_PATH, encoding='utf-8') as fh:
        return fh.read()


def save_game(player, rooms, current_room):
    """Returns None on success, or a message explaining what went wrong."""
    try:
        _write(json.dumps(snapshot(player, rooms, current_room)))
        return None
    except (OSError, TypeError, ValueError) as err:
        return str(err)


def load_game():
    """Returns (player, rooms, current_room), or (None, message)."""
    try:
        text = _read()
    except OSError as err:
        return None, str(err)
    if not text:
        return None, "no save found"
    try:
        return restore(json.loads(text)), None
    except (ValueError, KeyError, TypeError) as err:
        return None, str(err)


def clear_save():
    """Throw away the current save, so a restart really starts over."""
    if SAVE_HOOK is not None:
        SAVE_HOOK('')
        return
    try:
        os.remove(DEFAULT_SAVE_PATH)
    except OSError:
        pass


def has_save():
    try:
        return bool(_read())
    except OSError:
        return False
