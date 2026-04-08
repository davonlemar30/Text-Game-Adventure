"""Loader/assembler for external room content."""

from content.rooms_data import ROOMS_CONTENT

VALID_DIRECTIONS = {'north', 'south', 'east', 'west'}


def _validate_rooms_content(content):
    if not isinstance(content, dict):
        raise ValueError('Rooms content root must be a dict of room_id -> room definition.')

    for room_id, room in content.items():
        if not isinstance(room, dict):
            raise ValueError(f"Room '{room_id}' must be an object/dict.")
        for req in ('name', 'description', 'exits'):
            if req not in room:
                raise ValueError(f"Room '{room_id}' is missing required field '{req}'.")
        if not isinstance(room['exits'], dict):
            raise ValueError(f"Room '{room_id}' field 'exits' must be a direction map.")

        for direction in room['exits']:
            if direction not in VALID_DIRECTIONS:
                raise ValueError(
                    f"Room '{room_id}' has invalid exit direction '{direction}'. "
                    f"Allowed: {sorted(VALID_DIRECTIONS)}"
                )

        for direction in room.get('locked_exits', {}):
            if direction not in VALID_DIRECTIONS:
                raise ValueError(
                    f"Room '{room_id}' has invalid locked exit direction '{direction}'. "
                    f"Allowed: {sorted(VALID_DIRECTIONS)}"
                )

    for room_id, room in content.items():
        for direction, target_id in room['exits'].items():
            if target_id not in content:
                raise ValueError(
                    f"Room '{room_id}' exit '{direction}' points to unknown room '{target_id}' (typo?)."
                )
        for direction, target_id in room.get('locked_exits', {}).items():
            if target_id not in content:
                raise ValueError(
                    f"Room '{room_id}' locked exit '{direction}' points to unknown room '{target_id}' (typo?)."
                )


def load_rooms():
    """Return runtime rooms structure expected by game logic.

    Runtime shape: {Display Room Name: room_dict} where exits use display names.
    """
    _validate_rooms_content(ROOMS_CONTENT)

    id_to_name = {room_id: room['name'] for room_id, room in ROOMS_CONTENT.items()}
    runtime_rooms = {}

    for room_id, room in ROOMS_CONTENT.items():
        name = room['name']
        runtime_rooms[name] = {
            'brief': room.get('brief', ''),
            'description': room['description'],
            'exits': {d: id_to_name[target_id] for d, target_id in room.get('exits', {}).items()},
            'locked_exits': {d: id_to_name[target_id] for d, target_id in room.get('locked_exits', {}).items()},
            'items': dict(room.get('items', {})),
            'objects': dict(room.get('objects', {})),
        }

    return runtime_rooms
