# Content Authoring Guide

Room content is data-driven and lives in `content/rooms_data.py` as `ROOMS_CONTENT`.

## Schema
Each room entry uses a machine ID key (snake_case), for example `entrance_hall`.

Required fields:
- `name`: display room name used by runtime logic/UI
- `description`: long room text
- `exits`: mapping of direction -> room_id

Optional fields:
- `brief`: short room-entry description
- `locked_exits`: mapping of direction -> room_id
- `items`: mapping of item display name -> item description
- `objects`: mapping of object display name -> examine text

## Example room
```python
'kitchen': {
    'name': 'Kitchen',
    'brief': 'Stripped bare. Chemical smell. Don\'t make sparks.',
    'description': 'You are in the Kitchen... ',
    'exits': {'north': 'living_room', 'east': 'study'},
    'locked_exits': {},
    'items': {'food supplies': 'A dented tin...'},
    'objects': {'stove': 'Old gas stove...'},
}
```

## Encounters
Encounters are configured in `game_v6.py` under `ENCOUNTER_CONFIGS` and mapped by display room names in `ROOM_ENTRY_CONFIG_ENCOUNTERS`.

When adding a room encounter:
1. Add room data in `content/rooms_data.py`
2. Ensure exits reference valid room IDs
3. Add encounter entry in `ENCOUNTER_CONFIGS` (if needed)
4. Map room display name in `ROOM_ENTRY_CONFIG_ENCOUNTERS`

## Canonical ID notes
- Gameplay logic uses canonical constants in `game_v6.py`:
  - `StoryFlag`
  - `StatusEffect`
  - `ItemId`
- Room content may use display-facing item names for text, but logic-facing checks normalize via alias layer.

## Common pitfalls
- Exit target typo (e.g., `studyy`) causes load-time validation error.
- Invalid direction (`northeast`) fails validation.
- Missing required fields (`name`, `description`, `exits`) fails validation.
- Encounter not firing usually means display room name mismatch in room-entry encounter map.
