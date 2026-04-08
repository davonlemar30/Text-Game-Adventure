# ============================================================
# ZOMBIE APOCALYPSE: THE MANSION — V3.0
# Text Adventure RPG | Davon Gass
# ============================================================
# WHAT'S NEW IN V3.0 vs V2.0 (Phase 2 Implementation):
#   - Dynamic room descriptions that react to story flags
#   - Timed ambient event system (atmospheric horror at turn milestones)
#   - Bathroom zombie moral dilemma (first major choice with long-term impact)
#   - Generator puzzle: use flashlight on generator → unlocks Lab Wing
#   - Lab Wing room + medical file: Subject 01 identity revelation
#   - Walkie-talkie NPC (survivor Maya, frequency 7.4) — NPC encounter system
#   - action_radio() — respond to Maya's broadcast
#   - Event triggers: reading docs unlocks new examine interactions
#   - Enhanced Barbados encounter: moral choices affect final outcome
#   - Reputation flags: showed_mercy, left_figure, knows_full_truth
#   - Progressive Kristy journal: second passage unlocks after full lore read
#   - 'start' and 'pull' verbs added for generator interaction
# ============================================================

import sys
import time


# ============================================================
# DISPLAY UTILITIES
# ============================================================

def typewriter(text, delay=0.025):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def slow_print(text, delay=0.025):
    typewriter(text, delay)

def separator():
    print("\n" + "─" * 55 + "\n")


# ============================================================
# PLAYER
# ============================================================

class Player:
    def __init__(self):
        self.core_stats = {
            'Agility':      10,
            'Strength':     10,
            'Intelligence': 10,
            'Endurance':    10,
            'Perception':   10,
            'Willpower':    10,
        }
        self.substats = {
            'Stealth':      {'value': 0, 'unlocked': False},
            'Melee Combat': {'value': 0, 'unlocked': False},
            'First Aid':    {'value': 0, 'unlocked': False},
            'Mechanics':    {'value': 0, 'unlocked': False},
            'Awareness':    {'value': 0, 'unlocked': False},
            'Lockpicking':  {'value': 0, 'unlocked': False},
        }
        # Hidden stats — affect the narrative, never shown directly
        self.hidden_stats = {
            'Survival Skill':   0,
            'Mental Stability': 10,
            'Alpha Awareness':  0,
        }
        # Survival — degrade over time
        self.survival = {
            'hunger': 100,
            'thirst': 100,
            'stress': 0,
        }
        self.inventory        = []
        self.read_documents   = []
        self.examined         = set()
        self.story_flags      = {}
        self.turns            = 0
        self.last_radio_turn  = -1   # tracks last time radio was used

    def unlock_substat(self, name, value=1):
        if name in self.substats:
            self.substats[name]['unlocked'] = True
            self.substats[name]['value'] = value
        else:
            self.substats[name] = {'value': value, 'unlocked': True}

    def has_item(self, item_name):
        return item_name.lower() in [i.lower() for i in self.inventory]

    def remove_item(self, item_name):
        for item in self.inventory:
            if item.lower() == item_name.lower():
                self.inventory.remove(item)
                return True
        return False

    def show_stats(self):
        separator()
        print("CORE STATS")
        for stat, val in self.core_stats.items():
            print(f"  {stat:<16} {val}")
        print("\nSUBSTATS")
        for stat, data in self.substats.items():
            if data['unlocked']:
                print(f"  {stat:<16} {data['value']}")
            else:
                print(f"  {stat:<16} [locked]")
        print("\nSURVIVAL")
        for stat, val in self.survival.items():
            filled = val // 10
            bar = '█' * filled + '░' * (10 - filled)
            print(f"  {stat:<10} {bar}  {val}/100")
        separator()

    def show_inventory(self):
        separator()
        if not self.inventory:
            slow_print("Your pockets are empty.")
        else:
            print("INVENTORY:")
            for item in self.inventory:
                print(f"  — {item}")
        separator()


# ============================================================
# READABLE DOCUMENTS
# ============================================================

DOCUMENTS = {
    "mel's notebook": {
        "title": "Mel's Notebook — Final Entry",
        "text": (
            "The handwriting is shaky, rushed. Ink smeared by what looks\n"
            "like a bloody fingerprint.\n\n"
            "  'March 16th — The compound is breaking down faster than\n"
            "  anticipated. Barbados' condition is deteriorating rapidly —\n"
            "  his symptoms match the advanced infected subjects. He still\n"
            "  believes he can reverse it. He can't.\n\n"
            "  He's becoming aggressive. Unpredictable.\n\n"
            "  If anyone finds this — do not approach him.\n"
            "  Barbados isn't human anymore. He's something else entirely.\n"
            "  Far more dangerous.\n\n"
            "  I was wrong to stay. I should have—'\n\n"
            "The entry cuts off. The rest of the page is blank."
        )
    },
    "research log": {
        "title": "Partially Burned Research Log",
        "text": (
            "The edges of every page are charred. Someone tried to\n"
            "destroy this before leaving.\n\n"
            "  'Subject 01 — stable. Alive. Neural activity fluctuating\n"
            "  beyond expected parameters. The compound is doing something\n"
            "  we didn't anticipate. Subject is different.\n\n"
            "  Subject 02 — A. Barbados. Self-administered high-dose.\n"
            "  Results: catastrophic.\n\n"
            "  The prototype was never meant for—'\n\n"
            "The final entry is violently scribbled out.\n"
            "Underneath the scribble, barely visible: 'I'm sorry.'"
        )
    },
    "elias's diary page": {
        "title": "Elias March — Diary Page",
        "text": (
            "Tucked inside a bloodstained robe near the operating table.\n\n"
            "  'I came here because I had no choice. Terminal diagnosis.\n"
            "  Dr. Barbados said the treatment was promising.\n"
            "  For a while... I believed him.\n\n"
            "  The pain is gone. I feel stronger. But something is wrong.\n"
            "  The shadows in the corners — they move when nothing is there.\n\n"
            "  Last night I saw him. Barbados. In the lab. Filling a syringe.\n"
            "  His hands were shaking. His eyes were wrong.\n\n"
            "  This is all wrong.\n"
            "  This is all—'\n\n"
            "The writing stops mid-sentence."
        )
    },
    "kristy's letter": {
        "title": "Kristy O'Hara — Final Letter",
        "text": (
            "A bloodstained letter, left in the centre of the living\n"
            "room floor. Left deliberately.\n\n"
            "  'If you're reading this, you made it further than I did.\n\n"
            "  Don't go to the quarantine room. I know how that sounds.\n"
            "  But I need you to understand: whatever is in that room\n"
            "  is not Dr. Barbados anymore.\n\n"
            "  I locked him inside. I watched through the door window\n"
            "  for three days. He doesn't pace. He doesn't rage.\n"
            "  He just waits. He is learning.\n\n"
            "  The key is in the study. If you're brave enough —\n"
            "  or desperate enough — to use it, you already know what\n"
            "  I couldn't bring myself to do.\n\n"
            "  I'm sorry I couldn't finish this.\n"
            "  — K. O'H'"
        )
    },
    "voice recorder": {
        "title": "Daniel Everett — Voice Recording",
        "text": (
            "The recorder is cracked, half-destroyed. You hold down play.\n"
            "Static. Then a voice — strained, barely holding together.\n\n"
            "  'This is Daniel. Daniel Everett. Lab assistant.\n"
            "  If you found this, Barbados is already gone.\n"
            "  Don't try to understand what he became — just run.\n\n"
            "  He started on me first. Said it was a lab accident.\n"
            "  But I saw his notes. I was always the first test.\n\n"
            "  I tried to destroy the samples. Too late.\n\n"
            "  If you find this — DO NOT let him turn you into\n"
            "  one of them. Whatever you are now... fight it.\n"
            "  Stay human.'\n\n"
            "The recording cuts to silence."
        )
    },
    "kristy's journal": {
        "title": "Kristy O'Hara — Personal Journal",
        "text": (
            "Leather-bound. Hidden under the mattress. Personal.\n\n"
            "  'Week 3 — I keep telling myself there's a line he won't\n"
            "  cross. Mel says I'm naive. Maybe he's right.\n\n"
            "  Week 5 — Barbados let in three more survivors today.\n"
            "  Infected. He called them willing participants.\n"
            "  They weren't willing. I didn't stop him.\n\n"
            "  Week 7 — Mel is dead. I watched it happen and I couldn't\n"
            "  move. I got Barbados into the quarantine room. I don't\n"
            "  know how. Adrenaline. Terror. Something else.\n\n"
            "  Week 8 — The scratching stopped for two days. I thought\n"
            "  it was over. Then it started again. Slower. Deliberate.\n"
            "  He's not trying to escape. He's practicing.\n\n"
            "  I'm not going to make it out of here. But maybe\n"
            "  someone else will. The key is in the study.\n"
            "  God help whoever uses it.'"
        )
    },
    # V3.0 NEW — unlocked in Lab Wing
    "medical file": {
        "title": "Patient File — Subject 01 (Classified)",
        "text": (
            "The red tape tears easily. Inside: a photograph — you.\n"
            "A different version of you. Before.\n\n"
            "  'Subject 01 — Davon Gass.\n"
            "  Admitted: Week 1.\n"
            "  Diagnosis: [REDACTED]\n"
            "  Treatment protocol: Barbados Compound, high-dose.\n\n"
            "  Week 3 — Subject showing accelerated recovery.\n"
            "  Anomalous strength readings. Elevated neural response.\n\n"
            "  Week 6 — Subject no longer responding to standard pain stimuli.\n"
            "  Dr. Barbados notes: 'Subject 01 is different. Keep monitoring.'\n\n"
            "  Week 7 — Subject placed in induced sleep. For observation.\n"
            "  Dr. Barbados notes: 'He must not wake until I understand\n"
            "  what he is becoming. Or what I have created.'\n\n"
            "  Week 8 — [NO FURTHER ENTRIES]'\n\n"
            "You are Subject 01.\n"
            "You have been asleep for eight weeks.\n"
            "You have been becoming something since the beginning."
        )
    },
    # V3.0 NEW — found in Lab Wing workstation
    "sample case": {
        "title": "Sample Container — Subject 01 Baseline",
        "text": (
            "The label is clinical, sterile:\n\n"
            "  'Subject 01 — Pre-compound baseline.\n"
            "  Blood type: O-neg. Neural profile: standard.\n"
            "  Collected Week 1.\n\n"
            "  Post-compound deviation: +340% neural sensitivity.\n"
            "  Compound absorption: complete. Irreversible.\n\n"
            "  Note: Subject 01 carries no zombie aggression markers.\n"
            "  The compound adapted to him, not the other way around.\n"
            "  He is not infected. He is something new entirely.\n\n"
            "  This is the result we were looking for.\n"
            "  This is what we were afraid of.'\n\n"
            "The case is empty. Whatever was inside it broke out.\n"
            "Or was removed.\n"
            "Or walked away on its own."
        )
    },
}


# ============================================================
# TIMED AMBIENT EVENTS
# ============================================================
# Each entry: (turn_threshold, message, requires_item_or_None, flag_to_set)

TIMED_EVENTS = [
    (
        5,
        "Somewhere above you, something shifts — a single heavy step.\n"
        "Then stillness. The house holds its breath.",
        None,
        None
    ),
    (
        10,
        "The lights stutter — one quick pulse of darkness and back.\n"
        "Your pulse spikes with them.",
        None,
        None
    ),
    (
        15,
        "Through the walls — slow, rhythmic. Scratching.\n"
        "Coming from somewhere west. Measured. Patient.",
        None,
        'heard_scratching'
    ),
    (
        20,
        "The walkie-talkie crackles once in your pocket.\n"
        "Static. Then a voice — barely audible:\n"
        "  '— anyone? If you can hear this —'\n"
        "It cuts to silence before you can respond.",
        'walkie-talkie',
        'heard_first_signal'
    ),
    (
        28,
        "A sound from outside. Far away — glass breaking.\n"
        "Then nothing. The world beyond the walls stays quiet.",
        None,
        None
    ),
    (
        38,
        "The walkie-talkie comes alive again. Clearer this time.\n"
        "A woman's voice — controlled, deliberate:\n"
        "  'We have a camp. Northwest of the city. Frequency 7.4.\n"
        "   Don't come alone. Don't come infected.'\n"
        "The transmission repeats twice, then cuts.\n"
        "(Type RADIO to attempt a response.)",
        'walkie-talkie',
        'heard_maya_broadcast'
    ),
    (
        50,
        "The scratching from the west wall has stopped.\n"
        "Somehow that is worse.",
        None,
        None
    ),
]

_fired_events = set()   # tracks which turn thresholds have already fired

def check_timed_events(player):
    """Fire narrative events at turn milestones. Each fires only once."""
    global _fired_events
    for (turn_thresh, message, req_item, flag) in TIMED_EVENTS:
        if player.turns >= turn_thresh and turn_thresh not in _fired_events:
            # If the event requires the player to have a specific item, check that
            if req_item and not player.has_item(req_item):
                continue  # not triggered yet — item not in possession
            _fired_events.add(turn_thresh)
            print()
            separator()
            slow_print(message)
            separator()
            if flag:
                player.story_flags[flag] = True


# ============================================================
# DYNAMIC ROOM DESCRIPTIONS
# ============================================================

def get_room_description(room_name, rooms, player):
    """Returns the base description, with context-sensitive addons based on story flags."""
    base = rooms[room_name]['description']
    flags = player.story_flags
    addons = []

    if room_name == 'Basement':
        if 'generator_started' in flags:
            addons.append(
                "The generator hums steadily in the alcove.\n"
                "The card reader on the east lab door glows green — it's powered now."
            )

    elif room_name == 'Entrance Hall':
        if 'quarantine_opened' in flags:
            addons.append(
                "The smell from the quarantine room drifts through from the living room.\n"
                "Even here, you can't escape it."
            )
        if 'knows_protagonist_is_subject_01' in flags:
            addons.append(
                "The scratch marks at the base of the front door catch your eye again.\n"
                "Were any of them like you? Or were they just trying to get away?"
            )

    elif room_name == 'Living Room':
        if 'found_kristys_warning' in flags and 'quarantine_opened' not in flags:
            addons.append(
                "Kristy said the key was in the study.\n"
                "The quarantine door to the west feels like a countdown now."
            )
        if 'quarantine_opened' in flags:
            addons.append(
                "The quarantine door stands open to the west.\n"
                "The smell from inside doesn't stay contained anymore.\n"
                "Whatever you came to do in there — it's done."
            )

    elif room_name == 'Study':
        if ('knows_about_compound' in flags and
                'found_mels_warning' in flags and
                'heard_daniels_warning' in flags):
            addons.append(
                "You've read enough now to understand what happened here.\n"
                "What was done. What you are.\n"
                "The research notes make a different kind of sense."
            )
        if 'safe_opened' in flags:
            addons.append("The wall safe hangs open. You've taken what was inside.")

    elif room_name == 'Master Bedroom':
        if 'bathroom_zombie_mercy' in flags:
            addons.append(
                "The silence from the bathroom is complete now.\n"
                "You did what had to be done. The silence is heavier for it."
            )
        if 'read_full_journal' in flags:
            addons.append(
                "You understand now why Kristy stayed as long as she did.\n"
                "She wasn't trapped. She was trying to protect whoever came next.\n"
                "She protected you."
            )

    elif room_name == 'Bathroom':
        if 'bathroom_zombie_mercy' in flags:
            addons.append(
                "The figure is gone. You did what you had to.\n"
                "The bathtub has a stain it didn't have before.\n"
                "Don't look at it."
            )
        elif 'bathroom_zombie_left' in flags:
            addons.append(
                "It's still there.\n"
                "Still slumped against the bathtub. Still watching the door.\n"
                "Still waiting."
            )

    elif room_name == 'Lab Wing':
        if 'read_medical_file' in flags:
            addons.append(
                "You know what this room is now.\n"
                "You know what you were when you came in here.\n"
                "You know what you are when you leave."
            )

    if addons:
        return base + "\n\n" + "\n\n".join(addons)
    return base


# ============================================================
# ROOMS
# ============================================================

def build_rooms():
    return {

        'Basement': {
            'exits': {'north': 'Entrance Hall'},
            'locked_exits': {'east': 'Lab Wing'},
            'description': (
                "You are in the Basement Lab.\n"
                "The air is thick — stale chemicals, dried blood, something rotten.\n"
                "A cold steel operating table sits in the centre, IV tubes dangling\n"
                "loose from a stand beside it. Nearby, an empty suspension tank looms,\n"
                "its reinforced glass fogged over, dark residue clinging to the inside.\n"
                "A heavy metal door to the east is labelled 'Lab Wing Access' — locked.\n"
                "Stairs lead north toward the rest of the house."
            ),
            'items': {
                "flashlight":         "A heavy-duty flashlight. Batteries still work.",
                "mel's notebook":     "A small blood-smeared notebook. Cover reads 'M. Peoples'.",
                "elias's diary page": "A torn page from what looks like a patient's diary.",
                "research log":       "A partially burned research log. Someone tried to destroy it.",
            },
            'objects': {
                "operating table": (
                    "A cold steel table with restraint marks worn into the sides.\n"
                    "The IV tubes are disconnected — not removed carefully. Ripped out.\n"
                    "Someone left in a hurry. Or was taken in a hurry."
                ),
                "suspension tank": (
                    "An empty reinforced glass tank, large enough for a person.\n"
                    "Dark residue clings to the inside. A discoloured ring on the\n"
                    "floor beneath it — liquid pooled here for a long time.\n"
                    "Whatever was kept inside was removed without being shut down properly."
                ),
                "blood trail": (
                    "A smear of dried blood leads away from the operating table,\n"
                    "disappearing into the shadows near the far wall.\n"
                    "Not fresh — but not old enough. Whoever left this, it wasn't long ago."
                ),
                "lab door": (
                    "Heavy steel. Labelled 'Lab Wing Access.'\n"
                    "A card reader is mounted on the wall beside it. Dark. No power.\n"
                    "The generator could change that."
                ),
                "medical cart": (
                    "An overturned cart near the generator alcove. Scattered syringes\n"
                    "on the floor. One still has residue inside it — dark, viscous.\n"
                    "You don't pick it up."
                ),
                "generator": (
                    "A large diesel generator against the far wall. Dormant.\n"
                    "There's a fuel gauge on the side — it reads a quarter tank.\n"
                    "There's a pull cord along the right side.\n"
                    "Enough fuel to run. It just needs to be started."
                ),
            }
        },

        'Entrance Hall': {
            'exits': {
                'south': 'Basement',
                'west':  'Parlor',
                'east':  'Cloakroom',
                'north': 'Living Room',
            },
            'description': (
                "You are in the Entrance Hall.\n"
                "A chandelier hangs above, crystals coated in dust and cobwebs.\n"
                "The front doors are barricaded — wooden planks nailed haphazardly\n"
                "across them. Scratch marks mar the base of the doors from the inside.\n"
                "A grand staircase leads up to the right, its railing splintered.\n"
                "Passages lead west to the parlour, east to a cloakroom, north deeper in."
            ),
            'items': {},
            'objects': {
                "front door": (
                    "Heavy wood, barricaded with planks and a rusted chain.\n"
                    "Scratch marks at the base — deep, ragged gouges made by fingernails.\n"
                    "Human fingernails. Something tried to get OUT, not in.\n"
                    "Through the gap in the planks: still, grey light. Silence.\n"
                    "For now."
                ),
                "scratch marks": (
                    "Long ragged gouges at floor level. Made by fingernails.\n"
                    "Multiple sets. Multiple people. They all faced the same direction —\n"
                    "toward the door. Toward outside.\n"
                    "None of them made it."
                ),
                "chandelier": (
                    "Once grand. Now sagging, several crystals missing.\n"
                    "It sways faintly even though there's no wind you can feel.\n"
                    "The chain holding it to the ceiling looks old."
                ),
                "staircase": (
                    "Wide stairs leading to the second floor. One baluster is missing,\n"
                    "another cracked. Dried blood on the third step — a dark smear\n"
                    "that trails upward and then stops."
                ),
                "bloodstain": (
                    "A dark stain on the floor near the front door, dried long ago.\n"
                    "The shape suggests someone sat here for a while. Bleeding.\n"
                    "Waiting for something that never came."
                ),
            }
        },

        'Parlor': {
            'exits': {'east': 'Entrance Hall'},
            'description': (
                "You are in the Parlor.\n"
                "Antique furniture sits under dusty white sheets — the room preserved\n"
                "like something no one wanted to disturb. A grand mirror hangs above\n"
                "a cold fireplace, cracked diagonally. A broken phonograph sits in\n"
                "the corner, needle stuck. The air is stale — aged wood and something\n"
                "faintly floral that has no business being here anymore."
            ),
            'items': {
                "guestbook": "A dust-covered guestbook from the entrance stand. Pages brittle.",
            },
            'objects': {
                "phonograph": (
                    "The needle is stuck in a groove. The record stopped long ago.\n"
                    "Someone set it playing deliberately before they left this room.\n"
                    "You wonder what the last song was."
                ),
                "mirror": (
                    "Cracked diagonally from top-right to bottom-left. Your reflection\n"
                    "is split — two versions of you, slightly offset from each other.\n"
                    "You look pale. Paler than you should.\n"
                    "You look away before the other one does."
                ),
                "fireplace": (
                    "Cold and long-dead. Grey ash in the grate.\n"
                    "Among the ash, a scrap of paper — burned almost completely.\n"
                    "You can make out a single word: 'Shelly.'"
                ),
                "armchair": (
                    "Dried blood on the right armrest. Not a lot — but deliberate.\n"
                    "Someone sat here, injured, and stayed for a while.\n"
                    "The indent in the cushion is still there."
                ),
                "tea set": (
                    "A tipped-over tea set on a small side table, cups shattered.\n"
                    "Whoever left didn't look back.\n"
                    "Tea stains on the tablecloth — long since dry."
                ),
            }
        },

        'Cloakroom': {
            'exits': {'west': 'Entrance Hall'},
            'description': (
                "You are in the Cloakroom.\n"
                "A narrow space lined with coat racks and a storage cabinet.\n"
                "Dust-covered coats hang lifelessly. The floor creaks underfoot.\n"
                "A small mirror hangs crookedly on the wall, cracked at one corner."
            ),
            'items': {},
            'objects': {
                "mirror": (
                    "Cracked at the corner. Your reflection is slightly distorted —\n"
                    "one eye lower than the other, your jaw at a wrong angle.\n"
                    "You know it's just the crack. You know that."
                ),
                "coats": (
                    "Old coats, thick with dust. One rack has a gap — a coat is\n"
                    "missing. Whoever took it left the hanger swinging slightly.\n"
                    "There's a set of keys in one of the remaining coat pockets.\n"
                    "House keys — no use to you."
                ),
                "cabinet": (
                    "A locked wooden storage cabinet against the far wall.\n"
                    "The lock is small — a basic padlock. You'd need something\n"
                    "thin and rigid to open it. Or the right key."
                ),
                "hat": (
                    "A hat on the floor, brim thick with dust. It's been there\n"
                    "for weeks. The owner didn't come back for it."
                ),
            }
        },

        'Living Room': {
            'exits': {
                'east':  'Entrance Hall',
                'south': 'Kitchen',
                'north': 'Master Bedroom',
            },
            'locked_exits': {'west': 'Quarantine Room'},
            'description': (
                "You are in the Living Room.\n"
                "A shattered television lies on its side. An overturned bookcase has\n"
                "scattered papers and broken frames across the floor. A photograph on\n"
                "the mantelpiece faces down. A crumpled letter sits in the centre of\n"
                "the floor — placed there deliberately, not dropped."
            ),
            'items': {
                "kristy's letter": "A bloodstained letter left in the middle of the floor.",
            },
            'objects': {
                "photograph": (
                    "A framed photo, face-down on the mantelpiece.\n"
                    "You turn it over: a man — younger, smiling — with a woman\n"
                    "and a small girl in front of a house. Somewhere warm.\n"
                    "On the back, in neat handwriting: 'We'll do this together.'\n"
                    "The man is Dr. Barbados. You don't know how you know that.\n"
                    "You just do."
                ),
                "quarantine door": (
                    "A heavy reinforced door set into the west wall.\n"
                    "A sliding bolt lock and a keyhole, both engaged.\n"
                    "The wood on the other side has been scored with deep lines —\n"
                    "long, deliberate scratches, evenly spaced. Like tally marks.\n"
                    "You count them before you can stop yourself.\n"
                    "Forty-three."
                ),
                "television": (
                    "The screen is caved in — something hit it hard.\n"
                    "A bloodstain on the corner. The plug is still in the wall."
                ),
                "bookcase": (
                    "Toppled. Books and papers everywhere. Among them, a loose\n"
                    "page from a research journal — equations you don't understand.\n"
                    "At the bottom, underlined three times: 'Do not proceed to Stage 3.'"
                ),
                "mantelpiece": (
                    "Cold stone. The photo and a layer of undisturbed dust.\n"
                    "One small handprint in the dust — too small to be an adult's."
                ),
            }
        },

        'Kitchen': {
            'exits': {
                'north': 'Living Room',
                'east':  'Study',
            },
            'description': (
                "You are in the Kitchen.\n"
                "The cabinets hang open and empty — stripped of anything useful.\n"
                "Some of the floorboards near the pantry door have collapsed inward.\n"
                "A faint chemical smell hangs in the air. Not food. Something piped.\n"
                "Be careful with anything that makes a spark."
            ),
            'items': {
                "food supplies": "A dented tin of canned goods and some sealed protein bars.",
                "water bottle":  "A full sealed water bottle. Heavy.",
            },
            'objects': {
                "cabinets": (
                    "Every shelf emptied. Someone was here before you and took\n"
                    "everything they could carry. They left in a hurry — one of\n"
                    "the cabinet doors is hanging off its hinge."
                ),
                "floorboards": (
                    "Several boards near the pantry have collapsed into a dark space\n"
                    "below. The gap isn't large enough to fit through. But the smell\n"
                    "coming up from it is bad — rot and standing water."
                ),
                "stove": (
                    "An old gas stove. One of the burner knobs is turned slightly —\n"
                    "not all the way, but enough. That explains the smell.\n"
                    "Don't use any open flame in this room."
                ),
                "sink": (
                    "Bone dry. Both taps open, nothing coming out.\n"
                    "A dead plant on the windowsill above it.\n"
                    "Through the window: the overgrown side garden. Empty."
                ),
            }
        },

        'Study': {
            'exits': {'west': 'Kitchen'},
            'description': (
                "You are in the Study.\n"
                "A cluttered desk covered in handwritten research notes. Bookshelves\n"
                "lining the walls, one toppled. A dark computer terminal sits on the\n"
                "desk — no power. One note is pinned to the wall, underlined twice:\n"
                "'Trust no one.'"
            ),
            'items': {
                "walkie-talkie":  "A military-grade walkie-talkie. Charged. Only static for now.",
                "quarantine key": "A heavy key on a red lanyard, labelled 'Q-ROOM'.",
                "voice recorder": "A cracked voice recorder. The indicator light is still blinking.",
            },
            'objects': {
                "desk": (
                    "Covered in research notes — handwritten, densely packed.\n"
                    "Cell diagrams. Equations. Phrases like 'Stage 2 replication'\n"
                    "and 'neural bridge — viable?' scattered through the pages.\n"
                    "The last page is blank except for four words, pressed hard\n"
                    "into the paper: 'What have I done.'"
                ),
                "terminal": (
                    "Dark. No power to this part of the house.\n"
                    "A sticky note on the screen, handwritten:\n"
                    "'Camera log — 3 entries. Remote access required.'\n"
                    "If the generator were running, you might be able to access it."
                ),
                "bookshelves": (
                    "Mostly medical and biology texts. One shelf has been swept\n"
                    "completely clear. In the gap, someone has scratched a single\n"
                    "word into the wood: 'RUN'"
                ),
                "research notes": (
                    "Dozens of loose pages. Neural pathway diagrams. Toxicology\n"
                    "reports. Then a shift — infection vectors. Reanimation timelines.\n"
                    "The handwriting gets messier toward the end.\n"
                    "The final few pages are written in something that isn't ink."
                ),
                "safe": (
                    "A small wall safe behind a pulled-aside shelf.\n"
                    "Combination lock. The dial has been spun back to zero.\n"
                    "You'd need the combination to open it."
                ),
            }
        },

        'Master Bedroom': {
            'exits': {
                'south': 'Living Room',
                'east':  'Bathroom',
            },
            'description': (
                "You are in the Master Bedroom.\n"
                "A large bed with torn sheets, half-pulled to the floor. The closet\n"
                "door hangs ajar. A bloody handprint is smeared down the wall beside\n"
                "the window, as if someone slid. Empty medication bottles on the\n"
                "nightstand. The room smells like something that ended badly."
            ),
            'items': {
                "first aid kit":    "A proper medical kit — bandages, antiseptic, sutures. Sealed.",
                "kristy's journal": "A leather-bound personal journal. There's dried blood on the cover.",
            },
            'objects': {
                "bloody handprint": (
                    "A single handprint on the wall, smeared downward.\n"
                    "Whoever left it was sliding — falling, or being pulled down.\n"
                    "The print is small. A woman's hand."
                ),
                "closet": (
                    "Slightly open. Inside: clothes still on hangers, shoes on the floor,\n"
                    "a scarf torn cleanly in half. Nothing obviously missing\n"
                    "except the person who wore these."
                ),
                "nightstand": (
                    "Three empty pill bottles — all prescribed to 'K. O'Hara.'\n"
                    "Anxiety. Insomnia. And a third one with a name you don't recognise.\n"
                    "All empty. Finished, not spilled."
                ),
                "window": (
                    "Cracked. Curtains drawn but light bleeds through the gap.\n"
                    "Through it: the overgrown garden, and beyond that — shapes.\n"
                    "Slow. Aimless. More than you can count from here.\n"
                    "They haven't noticed the house yet."
                ),
            }
        },

        'Bathroom': {
            'exits': {'west': 'Master Bedroom'},
            'description': (
                "You are in the Bathroom.\n"
                "A cracked mirror above a dry sink. The tiles are stained.\n"
                "A figure in a hospital gown is slumped against the bathtub — still,\n"
                "for now. The smell in here is very bad.\n"
                "Move carefully."
            ),
            'items': {},
            'objects': {
                "mirror": (
                    "Cracked in several places. Your reflection fragments across\n"
                    "the breaks — pale, hollow, fractured.\n"
                    "One of the reflections doesn't quite line up with the others.\n"
                    "You tell yourself it's the angle."
                ),
                "figure": (
                    "A zombie. Former patient — hospital gown, bare feet, IV port\n"
                    "still taped to its arm. It stirs slightly when you get close.\n"
                    "Not aggressive. Not yet. But it will be if you make noise.\n"
                    "It was a person once. Not long ago."
                ),
                "sink": (
                    "Bone dry. Tap rusted open, nothing coming out.\n"
                    "There's a ring of grime where water used to reach."
                ),
                "medicine cabinet": (
                    "Above the sink, door hanging open.\n"
                    "Empty — mostly. One unused syringe, still in packaging.\n"
                    "You leave it where it is."
                ),
                "bathtub": (
                    "Dry. A dark ring marks the old waterline.\n"
                    "The bottom is stained in a way that suggests it wasn't just water\n"
                    "in here toward the end."
                ),
            }
        },

        'Quarantine Room': {
            'exits': {'east': 'Living Room'},
            'description': (
                "You are in the Quarantine Room.\n"
                "The walls are covered in long, deliberate scratch marks — not frantic\n"
                "clawing, but measured, evenly spaced lines. Tally marks. The decay\n"
                "smell is overwhelming. The room is dark beyond what your flashlight\n"
                "reaches. You can hear breathing. Slow. Patient."
            ),
            'items': {},
            'objects': {
                "scratch marks": (
                    "Rows of parallel lines etched deep into the plaster.\n"
                    "You count them. You stop counting.\n"
                    "You don't want to know how long he's been in here."
                ),
                "darkness": (
                    "The corners of the room are absolute black.\n"
                    "You can't see what's there.\n"
                    "But you can hear it breathing."
                ),
                "barbados": (
                    "He's here. Still — until he isn't.\n"
                    "His eyes catch your light: pale, luminous, aware.\n"
                    "He turns toward you slowly, like someone who has all the time\n"
                    "in the world. Like someone who has been waiting specifically for you.\n"
                    "He knows you're here. He knew before you opened the door."
                ),
            }
        },

        # ─── V3.0 NEW ROOM ───────────────────────────────────────
        'Lab Wing': {
            'exits': {'west': 'Basement'},
            'description': (
                "You are in the Lab Wing.\n"
                "A secondary research space — smaller, more clinical than the basement.\n"
                "Steel cabinets line the walls. Most are sealed. A single workstation\n"
                "glows dimly on backup power. A glass specimen case sits on a central\n"
                "table — broken open from the inside.\n"
                "The air is colder here. Wrong cold."
            ),
            'items': {
                "medical file": "A sealed medical file, red-taped. Your name is on the outside.",
                "sample case":  "A cracked specimen container labelled 'Subject 01 — Baseline.'",
            },
            'objects': {
                "workstation": (
                    "A terminal on backup power. The screen shows a log entry:\n"
                    "  'Subject 01 — status: AWOL.\n"
                    "   Last reading: off-chart neural activity.\n"
                    "   Recommend immediate containment if located.'\n"
                    "A camera feed shows four rooms. Three are dark.\n"
                    "One isn't. The Quarantine Room.\n"
                    "Something moves in the corner of the frame."
                ),
                "specimen case": (
                    "Reinforced glass — designed to hold biohazardous material.\n"
                    "Something broke out from inside. The edges of the glass are\n"
                    "pushed outward. There are bloodstains on the table — old ones.\n"
                    "And new ones.\n"
                    "The label reads: 'Subject 01 — Baseline Sample.'"
                ),
                "cabinets": (
                    "Most sealed with biohazard locks. One stands open — emptied.\n"
                    "On the shelf inside, scratched into the metal:\n"
                    "'He knows you're coming.'"
                ),
                "camera feed": (
                    "Four split-screen feeds. Three rooms dark.\n"
                    "Quarantine Room: visible. Something in the corner — not moving.\n"
                    "Waiting.\n"
                    "The timestamp on the feed reads: 8 weeks ago. Looping."
                ),
            }
        },
    }


# ============================================================
# PARSER
# ============================================================

def parse(raw_input):
    text = raw_input.strip().lower()
    if not text:
        return (None, None)

    # Single-word or fixed commands
    if text in ('i', 'inv', 'inventory'):
        return ('inventory', None)
    if text in ('stats', 'status'):
        return ('stats', None)
    if text in ('help', 'instructions', 'show instructions', '?'):
        return ('help', None)
    if text in ('look', 'l', 'look around', 'search room', 'examine room'):
        return ('look', None)
    if text in ('quit', 'exit', 'q'):
        return ('quit', None)
    if text in ('radio', 'respond', 'broadcast', 'call out', 'transmit', 'answer radio'):
        return ('radio', None)

    words = text.split()
    verb  = words[0]
    rest  = ' '.join(words[1:]) if len(words) > 1 else ''

    # Movement
    if verb in ('go', 'walk', 'move', 'head', 'travel', 'run'):
        dir_map = {
            'n': 'north', 'north': 'north',
            's': 'south', 'south': 'south',
            'e': 'east',  'east':  'east',
            'w': 'west',  'west':  'west',
        }
        dir_word = rest.split()[0] if rest else ''
        return ('go', dir_map.get(dir_word, dir_word))

    # Shorthand direction movement
    if verb in ('north', 'south', 'east', 'west', 'n', 's', 'e', 'w'):
        dir_map = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west'}
        return ('go', dir_map.get(verb, verb))

    # Examine / look at / inspect
    if verb in ('examine', 'look', 'inspect', 'check', 'search', 'study'):
        target = rest
        if rest.startswith('at '):
            target = rest[3:]
        if target and target not in ('around', 'room', 'here', ''):
            return ('examine', target)
        return ('look', None)

    # Read
    if verb == 'read':
        return ('read', rest)

    # Pick up — handle "pick up X"
    if verb in ('get', 'take', 'grab', 'pick', 'collect', 'retrieve'):
        if rest.startswith('up '):
            rest = rest[3:]
        return ('get', rest)

    # Drop
    if verb in ('drop', 'discard', 'leave', 'put down'):
        return ('drop', rest)

    # Use X on Y  /  use X
    if verb == 'use':
        if ' on ' in rest:
            parts = rest.split(' on ', 1)
            return ('use', (parts[0].strip(), parts[1].strip()))
        return ('use', (rest, None))

    # Open
    if verb == 'open':
        return ('open', rest)

    # Eat / drink
    if verb in ('eat', 'consume'):
        return ('eat', rest)
    if verb == 'drink':
        return ('drink', rest)

    # Unlock
    if verb == 'unlock':
        return ('use', (rest, 'door'))

    # V3.0: Start / pull — for generator
    if verb in ('start', 'pull', 'activate', 'crank', 'yank'):
        return ('start', rest if rest else 'generator')

    # V3.0: Radio
    if verb in ('radio', 'respond', 'broadcast', 'transmit'):
        return ('radio', rest)

    return ('unknown', text)


# ============================================================
# ACTIONS
# ============================================================

def action_look(room_name, rooms, player):
    room = rooms[room_name]
    separator()
    slow_print(get_room_description(room_name, rooms, player))

    if room.get('items'):
        print()
        item_names = list(room['items'].keys())
        if len(item_names) == 1:
            slow_print(f"You notice a {item_names[0]} here.")
        else:
            slow_print("You notice: " + ", ".join(f"a {i}" for i in item_names) + ".")

    all_exits = list(room.get('exits', {}).keys())
    locked    = [f"{d} (locked)" for d in room.get('locked_exits', {}).keys()]
    if all_exits or locked:
        slow_print("Exits: " + ", ".join(all_exits + locked) + ".")

    separator()


def action_examine(target, room_name, rooms, player):
    room = rooms[room_name]

    # ── V3.0: Bathroom zombie moral dilemma ──────────────────────
    if room_name == 'Bathroom' and target in ('figure', 'zombie', 'person', 'body'):
        if 'bathroom_zombie_resolved' not in player.story_flags:
            _bathroom_zombie_dilemma(room_name, rooms, player)
            return
        else:
            # Already resolved — show updated description
            if 'bathroom_zombie_mercy' in player.story_flags:
                separator()
                slow_print(
                    "There's nothing left to see here.\n"
                    "What you did was mercy. You keep telling yourself that."
                )
                separator()
            else:
                separator()
                slow_print(
                    "It's still there. Still watching you from the floor.\n"
                    "It hasn't moved toward you. But it hasn't looked away either."
                )
                separator()
            return

    # ── V3.0: Generator interaction ──────────────────────────────
    if target in ('generator',) and room_name == 'Basement':
        separator()
        if 'generator_started' in player.story_flags:
            slow_print(
                "The generator runs steadily. The lab door to the east is powered.\n"
                "You've done what you needed to do here."
            )
        else:
            slow_print(
                "A large diesel generator. The fuel gauge reads a quarter tank — enough.\n"
                "There's a pull cord along the right side. It looks stiff, like it\n"
                "hasn't been used in weeks.\n"
                "You could try to START it, or USE your FLASHLIGHT on it for better light."
            )
        separator()
        player.examined.add(target)
        return

    player.examined.add(target)

    # Check objects in room
    for obj_name, obj_desc in room.get('objects', {}).items():
        if target in obj_name or obj_name in target:
            separator()
            slow_print(obj_desc)
            separator()
            return

    # Check items in room
    for item_name, item_desc in room.get('items', {}).items():
        if target in item_name or item_name in target:
            separator()
            slow_print(item_desc)
            if item_name.lower() in DOCUMENTS:
                slow_print(f"\n(You can READ the {item_name} after picking it up.)")
            else:
                slow_print(f"\n(Type GET {item_name} to pick it up.)")
            separator()
            return

    # Check inventory
    for item in player.inventory:
        if target in item.lower() or item.lower() in target:
            separator()
            if item.lower() in DOCUMENTS:
                slow_print(f"A {item}. You could READ it.")
            else:
                slow_print(f"You examine the {item}. It seems useful — hold onto it.")
            separator()
            return

    slow_print(f"You don't see anything called '{target}' here.")


def _bathroom_zombie_dilemma(room_name, rooms, player):
    """V3.0 — The first major moral choice."""
    separator()
    slow_print(
        "It's a former patient — hospital gown, bare feet, IV port still taped\n"
        "to its arm. It stirs when you get close, but doesn't lunge.\n"
        "Its eyes find you — clouded, but there's something still in there.\n"
        "Some small, failing awareness. It used to be a person.\n"
        "It used to be here for the same reason you were."
    )
    print()
    slow_print("You could end its suffering. It won't last much longer anyway.")
    slow_print("Or you could leave it. Not every call is yours to make.")
    print()

    while True:
        choice = input("  [1] End it — a mercy kill\n"
                       "  [2] Leave it — not your call\n"
                       "  > ").strip()
        if choice in ('1', '2'):
            break
        slow_print("Choose 1 or 2.")

    print()

    if choice == '1':
        slow_print("You do what has to be done.")
        slow_print("It's quick. It's quiet. It's as clean as you can manage.")
        print()
        slow_print("Your hands won't stop shaking for the next few minutes.")
        slow_print("You weren't sure you could do that.")
        slow_print("You weren't sure you were the kind of person who could.")
        slow_print("Now you know.")
        player.story_flags['bathroom_zombie_resolved'] = True
        player.story_flags['bathroom_zombie_mercy']    = True
        player.story_flags['showed_mercy']             = True
        player.hidden_stats['Mental Stability']        = max(0,
            player.hidden_stats['Mental Stability'] - 2)
        player.hidden_stats['Alpha Awareness']         += 1
        player.hidden_stats['Survival Skill']          += 1
        # Remove the figure from the room objects
        rooms['Bathroom']['objects'].pop('figure', None)
    else:
        slow_print("You step back.")
        slow_print("Some things aren't yours to decide.")
        slow_print("It watches you leave. Something in those clouded eyes tracks you")
        slow_print("all the way to the door.")
        player.story_flags['bathroom_zombie_resolved'] = True
        player.story_flags['bathroom_zombie_left']     = True
        player.hidden_stats['Mental Stability']        = max(0,
            player.hidden_stats['Mental Stability'] - 1)

    separator()


def action_read(target, room_name, rooms, player):
    # Must have item in inventory to read
    for item in player.inventory:
        if target in item.lower() or item.lower() in target:
            if item.lower() in DOCUMENTS:
                doc = DOCUMENTS[item.lower()]
                separator()
                slow_print(f"[ {doc['title']} ]")
                print()
                slow_print(doc['text'])
                separator()
                if item.lower() not in player.read_documents:
                    player.read_documents.append(item.lower())
                    _on_read(item.lower(), player)
                return
            else:
                slow_print(f"There's nothing to read on the {item}.")
                return

    # Item in room but not picked up
    for item_name in rooms[room_name].get('items', {}).keys():
        if target in item_name or item_name in target:
            slow_print(f"Pick it up first. (GET {item_name})")
            return

    slow_print(f"You don't see a '{target}' to read.")


def _on_read(doc_name, player):
    """Story flags and hidden stat shifts triggered by reading documents."""
    if doc_name == "mel's notebook":
        player.story_flags['found_mels_warning']        = True
        player.hidden_stats['Mental Stability']         -= 1
    if doc_name == "research log":
        player.story_flags['knows_about_compound']      = True
        player.story_flags['knows_protagonist_is_subject_01'] = True
        slow_print("\n[Something about this hits differently. You've seen your own name somewhere.]")
    if doc_name == "elias's diary page":
        player.story_flags['knows_barbados_self_injected'] = True
    if doc_name == "kristy's letter":
        player.story_flags['found_kristys_warning']     = True
        player.story_flags['knows_key_in_study']        = True
    if doc_name == "voice recorder":
        player.story_flags['heard_daniels_warning']     = True
        player.hidden_stats['Alpha Awareness']          += 1
    if doc_name == "kristy's journal":
        player.story_flags['read_full_journal']         = True
        player.hidden_stats['Alpha Awareness']          += 2
    if doc_name == "medical file":
        player.story_flags['read_medical_file']         = True
        player.story_flags['knows_full_truth']          = True
        player.hidden_stats['Alpha Awareness']          += 3
        player.hidden_stats['Mental Stability']         = max(0,
            player.hidden_stats['Mental Stability'] - 2)
        slow_print("\n[You understand now. All of it. What was done to you. What you are.]")
    if doc_name == "sample case":
        player.story_flags['knows_compound_irreversible'] = True
        player.hidden_stats['Alpha Awareness']           += 1


def action_get(target, room_name, rooms, player):
    room = rooms[room_name]
    for item_name in list(room['items'].keys()):
        if target in item_name or item_name in target:
            player.inventory.append(item_name)
            del room['items'][item_name]
            slow_print(f"You pick up the {item_name}.")
            _on_pickup(item_name, player)
            return
    slow_print(f"There's no '{target}' here to pick up.")


def _on_pickup(item_name, player):
    if item_name == "first aid kit":
        if not player.substats['First Aid']['unlocked']:
            player.unlock_substat('First Aid', 1)
            slow_print("[First Aid substat unlocked.]")
    if item_name == "walkie-talkie":
        player.story_flags['has_comms'] = True
        slow_print("It hisses with static. Something is out there on the frequencies.")
    if item_name == "quarantine key":
        slow_print("Your hand is unsteady as you pick it up.")
        slow_print("You know what this opens.")
    if item_name == "medical file":
        slow_print("Your name is on the outside.")
        slow_print("Your hands go still.")
        slow_print("You already know this is going to change things.")
    if item_name == "flashlight":
        if not player.substats['Awareness']['unlocked']:
            player.unlock_substat('Awareness', 1)
            slow_print("[Awareness substat unlocked.]")


def action_go(direction, room_name, rooms, player):
    if not direction:
        slow_print("Go where? (north, south, east, west)")
        return room_name

    room    = rooms[room_name]
    exits   = room.get('exits', {})
    locked  = room.get('locked_exits', {})

    if direction in exits:
        new_room = exits[direction]
        return new_room

    if direction in locked:
        target_room = locked[direction]

        if target_room == 'Quarantine Room':
            if player.has_item('quarantine key'):
                slow_print("You slide the quarantine key into the lock. It turns.")
                slow_print("The bolt slides back. You push the door open.")
                slow_print("The smell hits you first.")
                player.story_flags['quarantine_opened'] = True
                exits[direction] = locked.pop(direction)
                return target_room
            else:
                slow_print("The door is locked with a heavy bolt and a keyhole.")
                if 'found_kristys_warning' in player.story_flags:
                    slow_print("Kristy said the key was in the study.")
                else:
                    slow_print("You can hear something on the other side. Slow. Deliberate.")
                return room_name

        if target_room == 'Lab Wing':
            if 'generator_started' in player.story_flags:
                slow_print("The card reader glows green. You push the door open.")
                exits[direction] = locked.pop(direction)
                return target_room
            else:
                slow_print("The card reader is dark. No power to this door.")
                slow_print("You need to get the generator running first.")
                return room_name

    slow_print("You can't go that way.")
    return room_name


def action_use(item, target, room_name, rooms, player):
    item_lower   = item.lower() if item else ''
    target_lower = target.lower() if target else ''

    if not player.has_item(item_lower) and item_lower not in ('flashlight',):
        found = False
        for inv_item in player.inventory:
            if item_lower in inv_item.lower():
                item_lower = inv_item.lower()
                found = True
                break
        if not found:
            slow_print(f"You're not carrying a '{item}'.")
            return

    # ── V3.0: Flashlight on generator ──────────────────────────
    if 'flashlight' in item_lower and ('generator' in target_lower or target_lower == ''):
        if room_name != 'Basement':
            slow_print("There's nothing useful to light up here.")
            return
        if 'generator_started' in player.story_flags:
            slow_print("The generator is already running.")
            return
        # Generator must have been examined first
        if 'generator' not in player.examined:
            slow_print("You'd want to examine the generator first.")
            return
        _start_generator(player, rooms)
        return

    if 'flashlight' in item_lower:
        slow_print("You click on the flashlight. The beam cuts sharply through the dark.")
        return

    if 'food' in item_lower:
        slow_print("You eat. Your body accepts it with something close to relief.")
        player.survival['hunger'] = min(100, player.survival['hunger'] + 35)
        player.remove_item('food supplies')
        return

    if 'water' in item_lower:
        slow_print("You drink. The dryness in your throat eases slightly.")
        player.survival['thirst'] = min(100, player.survival['thirst'] + 40)
        player.remove_item('water bottle')
        return

    if 'first aid' in item_lower:
        slow_print("You treat your wounds methodically. It helps more than you expected.")
        player.survival['stress'] = max(0, player.survival['stress'] - 20)
        return

    if 'quarantine key' in item_lower:
        slow_print("Try going west to use it on the quarantine room door.")
        return

    slow_print(f"You're not sure how to use that" + (f" on {target}." if target else "."))


def action_start(target, room_name, rooms, player):
    """V3.0 — Generator start via pull cord."""
    if room_name != 'Basement':
        slow_print("There's nothing here to start.")
        return
    if 'generator_started' in player.story_flags:
        slow_print("The generator is already running.")
        return
    if 'generator' not in player.examined:
        slow_print("You should examine the generator first before attempting to start it.")
        return
    if not player.has_item('flashlight'):
        slow_print(
            "You need better light to find the pull cord properly.\n"
            "Try: USE FLASHLIGHT ON GENERATOR"
        )
        return
    _start_generator(player, rooms)


def _start_generator(player, rooms):
    """V3.0 — Narrative sequence for starting the generator."""
    separator()
    slow_print("You brace the flashlight against your shoulder, freeing both hands.")
    time.sleep(0.3)
    slow_print("The pull cord is stiff — weeks of cold have tightened it.")
    time.sleep(0.4)
    slow_print("First pull: nothing.")
    time.sleep(0.5)
    slow_print("Second: a cough, a choke.")
    time.sleep(0.4)
    slow_print("Third —")
    time.sleep(0.6)
    slow_print("The generator shudders, protests, and catches.")
    time.sleep(0.3)
    slow_print("It runs.")
    print()
    slow_print("Lights flicker on across the basement. The card reader on the east\n"
               "door blinks from red to green.")
    print()
    slow_print("Lab Wing Access — now open.")
    separator()
    player.story_flags['generator_started'] = True
    if not player.substats['Mechanics']['unlocked']:
        player.unlock_substat('Mechanics', 1)
        slow_print("[Mechanics substat unlocked.]")
    # Permanently unlock the east exit
    basement = rooms['Basement']
    if 'east' in basement.get('locked_exits', {}):
        basement['exits']['east'] = basement['locked_exits'].pop('east')


def action_eat(target, player):
    if 'food' in target:
        action_use('food supplies', None, None, None, player)
    else:
        slow_print(f"You don't have any '{target}' to eat.")


def action_drink(target, player):
    if 'water' in target:
        action_use('water bottle', None, None, None, player)
    else:
        slow_print(f"You don't have any '{target}' to drink.")


def action_drop(target, room_name, rooms, player):
    for item in list(player.inventory):
        if target in item.lower() or item.lower() in target:
            player.inventory.remove(item)
            rooms[room_name]['items'][item] = "Something you set down."
            slow_print(f"You set down the {item}.")
            return
    slow_print(f"You're not carrying a '{target}'.")


def action_radio(player):
    """V3.0 — Walkie-talkie NPC interaction with Maya."""
    if not player.has_item('walkie-talkie'):
        slow_print("You're not carrying anything to broadcast on.")
        return

    if 'heard_first_signal' not in player.story_flags and \
       'heard_maya_broadcast' not in player.story_flags:
        slow_print("Only static. You haven't picked up any signal yet.")
        return

    # Cooldown — limit radio spam
    if player.turns - player.last_radio_turn < 5:
        slow_print("Static. You don't hear anything back yet.")
        return

    separator()
    player.last_radio_turn = player.turns

    if 'maya_responded' not in player.story_flags:
        # First real exchange
        slow_print("You key the transmit button.")
        slow_print("  'This is — I'm in the mansion. Northwest of town.\n"
                   "  I'm alive. I need a route out.'")
        time.sleep(0.8)
        print()
        slow_print("Static. Then:")
        time.sleep(0.6)
        slow_print("  [MAYA]: 'Copy that. We tracked this signal two days ago —\n"
                   "   thought it was dead. My name's Maya. We're about four\n"
                   "   kilometres northwest. Old community centre.\n\n"
                   "   Listen to me carefully: whatever is in that building\n"
                   "   with you — do not engage it directly. It knows you're there.\n"
                   "   It's been waiting.\n\n"
                   "   If you can get out — just run. Come to us.\n"
                   "   Frequency 7.4. We'll be listening.'")
        print()
        slow_print("The transmission holds for a moment. Then:")
        slow_print("  [MAYA]: 'Are you... are you infected?'")
        time.sleep(0.5)
        print()

        while True:
            resp = input("  [1] 'No. I'm clean.'\n"
                         "  [2] 'I don't know what I am.'\n"
                         "  > ").strip()
            if resp in ('1', '2'):
                break
            slow_print("Choose 1 or 2.")

        print()
        if resp == '1':
            slow_print("  [MAYA]: 'Good. Then get out of there.\n"
                       "   We'll have a team ready when you arrive.'")
            player.story_flags['told_maya_clean'] = True
        else:
            slow_print("  [MAYA]: '...\n"
                       "   Then you're exactly who we've been looking for.\n"
                       "   Get out of there. Now. Come to us.\n"
                       "   There are things you need to know.'")
            player.story_flags['told_maya_unknown'] = True
            player.hidden_stats['Alpha Awareness'] += 1

        player.story_flags['maya_responded'] = True
        player.story_flags['knows_camp_location'] = True

    else:
        # Subsequent calls
        slow_print("You key the transmit button.")
        time.sleep(0.5)
        slow_print("  [MAYA]: 'Still receiving you. Get out of that building.\n"
                   "   We'll be on 7.4. Don't take longer than you have to.'")

    separator()


# ============================================================
# SURVIVAL SYSTEM
# ============================================================

def update_survival(player):
    player.turns += 1

    if player.turns % 8 == 0:
        player.survival['hunger'] -= 3
        player.survival['thirst'] -= 5
        player.survival['stress']  = min(100, player.survival['stress'] + 1)

    if player.survival['hunger'] <= 20:
        slow_print("Your stomach cramps painfully. You need to eat something.")
    if player.survival['thirst'] <= 20:
        slow_print("Your throat is raw. You need water.")
    if player.survival['stress'] >= 70:
        slow_print("Your hands won't stop shaking. Keep it together.")

    if player.survival['stress'] >= 80:
        player.hidden_stats['Mental Stability'] = max(0,
            player.hidden_stats['Mental Stability'] - 1)

    # Death conditions
    if player.survival['hunger'] <= 0:
        separator()
        slow_print("Your body gives out. It's quiet at least.")
        slow_print("You never find out what's waiting upstairs.")
        slow_print("\n— GAME OVER —\n")
        separator()
        sys.exit()

    if player.survival['thirst'] <= 0:
        separator()
        slow_print("Your vision whites out. Your legs stop working.")
        slow_print("You collapse on the floor of the mansion.")
        slow_print("\n— GAME OVER —\n")
        separator()
        sys.exit()

    # Check timed events
    check_timed_events(player)


# ============================================================
# FINAL ENCOUNTER — BARBADOS (V3.0 ENHANCED)
# ============================================================

def encounter_barbados(player):
    separator()
    slow_print("Barbados moves.")
    time.sleep(0.5)
    slow_print("Not fast — but with terrible purpose.")
    time.sleep(0.3)
    slow_print("His eyes find you in the dark. Pale. Luminous. Knowing.")
    print()
    time.sleep(0.6)

    required = ['flashlight', 'first aid kit', 'food supplies',
                'walkie-talkie', 'quarantine key']
    has_all         = all(player.has_item(r) for r in required)
    read_warning    = 'found_kristys_warning'               in player.story_flags
    knows_truth     = 'knows_barbados_self_injected'        in player.story_flags
    knows_compound  = 'knows_protagonist_is_subject_01'     in player.story_flags
    knows_full      = 'knows_full_truth'                    in player.story_flags
    showed_mercy    = 'showed_mercy'                        in player.story_flags
    has_camp        = 'knows_camp_location'                 in player.story_flags

    # ── V3.0 BEST ENDING: knows everything, has everything, made contact ──
    if has_all and knows_full and has_camp:
        slow_print("You came prepared. You understand what he is — and what you are.")
        slow_print("More than that: you know there's somewhere to go after this.")
        print()
        if showed_mercy:
            slow_print("When Barbados lunges, you don't flinch.")
            slow_print("You showed mercy in that bathroom. You know the cost of hesitation.")
            slow_print("You also know it was the right call.")
            slow_print("This is a different call.")
        else:
            slow_print("When Barbados lunges, something in you responds.")
            slow_print("Not fear. Recognition.")
        print()
        slow_print("You use everything you've gathered and everything you've learned.")
        slow_print("The fight is unlike anything you've ever done.")
        slow_print("It isn't clean. But you walk out.")
        print()
        slow_print("You move northwest. Four kilometres.")
        slow_print("Maya's voice crackles through the walkie-talkie as you reach\n"
                   "the community centre's outer gate: 'I see you. Come in.'")
        print()
        slow_print("There are things that need answers.")
        slow_print("You carry the only ones that matter.")
        print()
        _ending_title("THE TRUTH — YOU CARRY IT NOW")

    # ── GOOD ENDING: fully prepared + knows core truth ──
    elif has_all and read_warning and knows_truth and knows_compound:
        slow_print("You came prepared. You understand what he is — and what was done to you.")
        print()
        slow_print("When Barbados lunges, something in you responds — not fear.")
        slow_print("Recognition.")
        print()
        slow_print("You use everything you've gathered and everything you've learned.")
        slow_print("The fight is brutal. He is stronger than anything human.")
        slow_print("So are you, in ways you're only beginning to understand.")
        print()
        slow_print("You walk out of the mansion as the grey sky begins to lighten.")
        slow_print("The world is broken. You carry a secret that could remake it.")
        slow_print("Or break it further.")
        print()
        _ending_title("ESCAPED — WITH THE TRUTH")

    # ── DECENT ENDING: prepared but missing full context ──
    elif has_all:
        slow_print("You have what you need to survive this — barely.")
        slow_print("The fight is brutal. He is stronger than anything human.")
        slow_print("But you make it out.")
        print()
        slow_print("You don't look back as you leave the mansion.")
        slow_print("You don't stop moving until the house is out of sight.")
        print()
        _ending_title("ESCAPED — FOR NOW")

    # ── BAD ENDING: unprepared ──
    else:
        missing = [r for r in required if not player.has_item(r)]
        slow_print("You are not ready for this.")
        print()
        slow_print(f"You're missing: {', '.join(missing)}.")
        print()

        if showed_mercy:
            slow_print("He crosses the room. You stand your ground — it's the only\n"
                       "thing you have left. It means nothing.")
        else:
            slow_print("He crosses the room faster than something dead should move.")

        slow_print("The last thing you see is his eyes — pale, aware, almost sad.")
        slow_print("Almost human.")
        print()
        slow_print("— GAME OVER —\n")
        separator()
        sys.exit()


def _ending_title(title):
    separator()
    pad = (55 - len(title)) // 2
    slow_print(" " * pad + title)
    separator()
    sys.exit()


# ============================================================
# OPENING SCENE
# ============================================================

def opening_scene():
    separator()
    lines = [
        "Darkness.",
        "",
        "Not the kind that clouds vision — the deeper kind.",
        "The kind that smothers thought.",
        "",
        "A pulse beats behind your eyes. Each throb drags sensation",
        "back into a body that feels foreign. Your breath is shallow —",
        "as if your lungs are relearning their purpose.",
        "",
        "The air is stale. Metallic. Blood and antiseptics gone sour.",
        "",
        "Cold steel presses against your back.",
        "",
        "  How long have I been lying here?",
        "",
        "Your fingers twitch. Needle marks. Bruises. Disconnected IV tubes.",
        "",
        "Fluorescent lights flicker above you. Cracks in the ceiling.",
        "Shadows at the edges of your vision — unmoving. Waiting.",
        "",
        "You try to sit up. Your body resists.",
        "",
        "Then —",
        "",
        "A slow creak from somewhere above.",
        "",
        "One step.",
        "",
        "Then another.",
        "",
        "Silence returns. Heavy. Knowing.",
        "",
        "You are not alone.",
    ]
    for line in lines:
        typewriter(line, 0.028)
        if line == "":
            time.sleep(0.08)
    separator()
    input("(Press Enter to begin...)\n")


def show_help():
    separator()
    print("HOW TO PLAY")
    print()
    print("  go [north/south/east/west]     move between rooms  (or just type: north)")
    print("  look                           look around the room")
    print("  examine [object]               examine something closely")
    print("  get [item]                     pick up an item")
    print("  read [item]                    read a document or note")
    print("  use [item]                     use an item")
    print("  use [item] on [target]         use an item on something")
    print("  start [generator]              start a machine (pull cord, etc.)")
    print("  radio                          attempt to broadcast on the walkie-talkie")
    print("  inventory  (or i)              check what you're carrying")
    print("  stats                          view your stats")
    print("  drop [item]                    drop an item")
    print("  help                           show this screen")
    print("  quit                           exit the game")
    separator()


# ============================================================
# MAIN LOOP
# ============================================================

def main():
    opening_scene()

    player  = Player()
    rooms   = build_rooms()
    current = 'Basement'

    show_help()
    action_look(current, rooms, player)

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            sys.exit()

        if not raw:
            continue

        verb, target = parse(raw)

        if verb == 'quit':
            slow_print("You close your eyes. The mansion holds its breath.")
            sys.exit()

        elif verb == 'look':
            action_look(current, rooms, player)

        elif verb == 'examine':
            if target:
                action_examine(target, current, rooms, player)
            else:
                action_look(current, rooms, player)

        elif verb == 'read':
            if target:
                action_read(target, current, rooms, player)
            else:
                slow_print("Read what?")

        elif verb == 'get':
            if target:
                action_get(target, current, rooms, player)
            else:
                slow_print("Get what?")

        elif verb == 'drop':
            if target:
                action_drop(target, current, rooms, player)
            else:
                slow_print("Drop what?")

        elif verb == 'inventory':
            player.show_inventory()

        elif verb == 'stats':
            player.show_stats()

        elif verb == 'help':
            show_help()

        elif verb == 'go':
            new_room = action_go(target, current, rooms, player)
            if new_room != current:
                current = new_room
                action_look(current, rooms, player)
                if current == 'Quarantine Room':
                    encounter_barbados(player)

        elif verb == 'use':
            if isinstance(target, tuple):
                action_use(target[0], target[1], current, rooms, player)
            elif target:
                action_use(target, None, current, rooms, player)
            else:
                slow_print("Use what?")

        elif verb == 'eat':
            if target:
                action_eat(target, player)
            else:
                slow_print("Eat what?")

        elif verb == 'drink':
            if target:
                action_drink(target, player)
            else:
                slow_print("Drink what?")

        elif verb == 'open':
            slow_print("Try: USE [key] ON [door], or just GO in a direction.")

        elif verb == 'start':
            action_start(target or 'generator', current, rooms, player)

        elif verb == 'radio':
            action_radio(player)

        elif verb == 'unknown':
            slow_print(f"You're not sure what '{target}' means. Type HELP for commands.")

        else:
            slow_print("The mansion waits. What do you do?")

        update_survival(player)


if __name__ == "__main__":
    main()
