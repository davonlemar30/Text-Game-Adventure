# ============================================================
# ZOMBIE APOCALYPSE: THE MANSION — V6.0
# Text Adventure RPG | Davon Gass
# ============================================================
# WHAT'S NEW IN V6.0 vs V5.0 (Playtest Pass 2):
#   - "Flashlight Beam" renamed to "Flash" — grounded, logical
#   - 8 total combat encounters spread across the mansion
#   - FIRST encounter now in Entrance Hall (unavoidable early fight)
#   - New encounters: Entrance Hall, Kitchen, Study, Master Bedroom
#     closet (burst zombie), Lab Wing (infected lab tech)
#   - New enemy types: Scavenger Zombie, Study Zombie,
#     Closet Zombie (priority burst), Lab Technician (Bio)
#   - Front door: clear messaging when player tries to open/use it
#   - Hidden objects: Parlor armchair reveals a survivor note
#     on close examination (new lore doc — Thomas Halley)
#   - Endings now reference actual player choices — mercy, Maya
#     dialogue, what you knew when you faced Barbados
#   - All V5 features fully preserved
# ============================================================

import sys
import time
import random


# ============================================================
# DISPLAY UTILITIES
# ============================================================

def typewriter(text, delay=0.025):
    """Typewriter effect — reserved for story moments."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def slow_print(text, delay=0.025):
    typewriter(text, delay)

def fast_print(text):
    """Instant print — used for room descriptions and most gameplay output."""
    print(text)

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
        self.hidden_stats = {
            'Survival Skill':   0,
            'Mental Stability': 10,
            'Alpha Awareness':  0,
        }
        self.survival = {
            'hunger': 100,
            'thirst': 100,
            'stress': 0,
        }
        # V5: Combat stats
        self.hp             = 50
        self.max_hp         = 50
        self.combat_attack  = 10
        self.combat_defense = 10
        self.player_type    = 'Alpha'
        self.combat_statuses = {}   # {status_name: turns_remaining}

        self.inventory       = []
        self.read_documents  = []
        self.examined        = set()
        self.story_flags     = {}
        self.turns           = 0
        self.last_radio_turn = -1
        self.visited_rooms   = set()
        self.notes = {
            'people': [],
            'clues':  [],
        }

    def add_note(self, category, entry):
        if entry not in self.notes.get(category, []):
            self.notes.setdefault(category, []).append(entry)

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
        print("\nCOMBAT")
        filled = int((self.hp / self.max_hp) * 10)
        bar = '█' * filled + '░' * (10 - filled)
        print(f"  {'HP':<10} {bar}  {self.hp}/{self.max_hp}")
        if self.combat_statuses:
            print(f"  Status: {', '.join(self.combat_statuses.keys())}")
        print("\nSURVIVAL")
        for stat, val in self.survival.items():
            filled = val // 10
            bar = '█' * filled + '░' * (10 - filled)
            print(f"  {stat:<10} {bar}  {val}/100")
        separator()

    def show_inventory(self):
        separator()
        if not self.inventory:
            print("Your pockets are empty.")
        else:
            print("INVENTORY:")
            for item in self.inventory:
                print(f"  — {item}")
        separator()


# ============================================================
# COMBAT SYSTEM — TYPES, MOVES, ENEMIES
# ============================================================

# TYPE_CHART[attacker_type][defender_type] = damage multiplier
TYPE_CHART = {
    'Brute':   {'Brute': 1.0, 'Alpha': 0.5, 'Psyche': 2.0, 'Bio': 1.0, 'Stealth': 0.5},
    'Alpha':   {'Brute': 2.0, 'Alpha': 1.0, 'Psyche': 1.0, 'Bio': 0.5, 'Stealth': 1.0},
    'Psyche':  {'Brute': 0.5, 'Alpha': 2.0, 'Psyche': 1.0, 'Bio': 1.0, 'Stealth': 0.5},
    'Bio':     {'Brute': 1.0, 'Alpha': 2.0, 'Psyche': 0.5, 'Bio': 1.0, 'Stealth': 1.0},
    'Stealth': {'Brute': 2.0, 'Alpha': 1.0, 'Psyche': 2.0, 'Bio': 0.5, 'Stealth': 1.0},
}


class Move:
    def __init__(self, name, move_type, power, accuracy,
                 effect=None, effect_chance=0.0, priority=0, description=''):
        self.name         = name
        self.move_type    = move_type
        self.power        = power
        self.accuracy     = accuracy
        self.effect       = effect          # 'blinded','infected','stressed','steadied','suppressed'
        self.effect_chance = effect_chance
        self.priority     = priority        # higher = goes first
        self.description  = description


class Enemy:
    def __init__(self, name, enemy_type, hp, attack, defense, speed, moves, is_boss=False):
        self.name       = name
        self.enemy_type = enemy_type
        self.hp         = hp
        self.max_hp     = hp
        self.attack     = attack
        self.defense    = defense
        self.speed      = speed
        self.moves      = moves
        self.is_boss    = is_boss
        self.statuses   = {}        # {status_name: turns_remaining}
        self.guarded    = False


# ──────────────────────────────────────
# Player move definitions
# ──────────────────────────────────────

PLAYER_MOVES = {
    'strike': Move(
        'Strike', 'Brute', 40, 0.95,
        description='Reliable physical damage.'
    ),
    'guard': Move(
        'Guard', 'Stealth', 0, 1.00,
        effect='steadied', effect_chance=1.0,
        description='Reduce next hit by 40%.'
    ),
    'flash': Move(
        'Flash', 'Psyche', 25, 0.85,
        effect='blinded', effect_chance=0.40,
        description='Shine the light directly in its eyes.'
    ),
    'static_pulse': Move(
        'Static Pulse', 'Psyche', 35, 0.80,
        effect='stressed', effect_chance=0.30,
        description='Psychic surge. May cause stress.'
    ),
    'alpha_sense': Move(
        'Alpha Sense', 'Alpha', 45, 0.90,
        description='Channel your Alpha nature.'
    ),
    'override': Move(
        'Override', 'Alpha', 0, 0.85,
        effect='suppressed', effect_chance=1.0,
        description='Suppress enemy next action.'
    ),
}


def get_available_moves(player):
    """Return list of move keys the player can currently use."""
    aa = player.hidden_stats['Alpha Awareness']
    moves = ['strike', 'guard']
    if player.has_item('flashlight'):
        moves.append('flash')
    if aa >= 3:
        moves.append('static_pulse')
    if aa >= 6:
        moves.append('alpha_sense')
    if aa >= 9:
        moves.append('override')
    return moves


# ──────────────────────────────────────
# Enemy factory functions
# ──────────────────────────────────────

def make_standard_zombie():
    return Enemy(
        name='Standard Zombie',
        enemy_type='Brute',
        hp=30, attack=8, defense=5, speed=4,
        moves=[
            Move('Shamble', 'Brute', 20, 0.80,
                 description='A lurching, clumsy attack.'),
            Move('Bite',    'Bio',   15, 0.75,
                 effect='infected', effect_chance=0.20,
                 description='Infected wound — may transmit.'),
        ]
    )


def make_patient_zombie():
    return Enemy(
        name='Patient Zero',
        enemy_type='Bio',
        hp=35, attack=9, defense=5, speed=3,
        moves=[
            Move('Scratch', 'Bio',  15, 0.90,
                 description='A raking claw strike.'),
            Move('Infect',  'Bio',  10, 0.70,
                 effect='infected', effect_chance=1.0,
                 description='Guaranteed infection if it lands.'),
        ]
    )


def make_barbados():
    return Enemy(
        name='Dr. Barbados',
        enemy_type='Alpha',
        hp=80, attack=20, defense=8, speed=9,
        moves=[
            Move('Crush',    'Brute',  35, 0.90,
                 description='A devastating physical blow.'),
            Move('Fracture', 'Psyche', 30, 0.85,
                 effect='stressed', effect_chance=1.0,
                 description='Psychic assault. Causes stress.'),
            Move('Lunge',    'Brute',  50, 0.90,
                 priority=2,
                 description='Desperate final charge — goes first.'),
        ],
        is_boss=True,
    )


def make_entrance_zombie():
    """Brute zombie blocking the Entrance Hall — first combat encounter."""
    return Enemy(
        name='Shambler',
        enemy_type='Brute',
        hp=28, attack=8, defense=5, speed=4,
        moves=[
            Move('Shove',  'Brute', 18, 0.85,
                 description='Knocks you back hard.'),
            Move('Bite',   'Bio',   15, 0.75,
                 effect='infected', effect_chance=0.20,
                 description='Infects the wound.'),
        ]
    )


def make_kitchen_zombie():
    """Scavenger zombie picked up in the kitchen."""
    return Enemy(
        name='Scavenger',
        enemy_type='Brute',
        hp=30, attack=8, defense=5, speed=5,
        moves=[
            Move('Shamble', 'Brute', 20, 0.80,
                 description='Lurching attack.'),
            Move('Bite',    'Bio',   15, 0.75,
                 effect='infected', effect_chance=0.20,
                 description='Infects the wound.'),
        ]
    )


def make_study_zombie():
    """Brute zombie hunched over the research papers."""
    return Enemy(
        name='Researcher',
        enemy_type='Brute',
        hp=30, attack=9, defense=5, speed=3,
        moves=[
            Move('Shamble', 'Brute', 20, 0.80,
                 description='Slow but relentless.'),
            Move('Bite',    'Bio',   14, 0.70,
                 effect='infected', effect_chance=0.15,
                 description='A ragged bite.'),
        ]
    )


def make_closet_zombie():
    """Burst zombie from Master Bedroom closet — priority first-turn lunge."""
    return Enemy(
        name='Closet Zombie',
        enemy_type='Brute',
        hp=22, attack=10, defense=4, speed=8,
        moves=[
            Move('Burst',   'Brute', 32, 0.90,
                 priority=1,
                 description='Explodes out of the closet — goes first.'),
            Move('Claw',    'Brute', 20, 0.85,
                 description='Frantic slashing.'),
        ]
    )


def make_lab_tech_zombie():
    """Infected lab technician — Bio type, more dangerous."""
    return Enemy(
        name='Lab Technician',
        enemy_type='Bio',
        hp=40, attack=10, defense=6, speed=5,
        moves=[
            Move('Needle',  'Bio',   18, 0.85,
                 effect='infected', effect_chance=0.35,
                 description='Still has the syringe. May infect.'),
            Move('Scratch', 'Bio',   15, 0.90,
                 description='Raking claw attack.'),
        ]
    )


# ──────────────────────────────────────
# Combat utilities
# ──────────────────────────────────────

def calc_damage(attacker_attack, power, defender_defense, type_mult):
    roll = random.uniform(0.85, 1.00)
    return max(1, int(attacker_attack * power / (defender_defense * 4) * type_mult * roll))


def hp_bar(current, maximum, width=10):
    pct    = max(0.0, current / maximum)
    filled = round(pct * width)
    return '█' * filled + '░' * (width - filled)


def display_battle_status(player, enemy):
    separator()
    enemy_bar = hp_bar(enemy.hp, enemy.max_hp)
    print(f"  {enemy.name.upper()}")
    print(f"  HP: {enemy_bar}  {enemy.hp}/{enemy.max_hp}   Type: {enemy.enemy_type}")
    if enemy.statuses:
        st = ', '.join(f"{s}({t}t)" for s, t in enemy.statuses.items())
        print(f"  Status: {st}")
    print()
    player_bar = hp_bar(player.hp, player.max_hp)
    print(f"  YOUR HP: {player_bar}  {player.hp}/{player.max_hp}")
    if player.combat_statuses:
        st = ', '.join(f"{s}({t}t)" for s, t in player.combat_statuses.items())
        print(f"  Status: {st}")
    print()


# ──────────────────────────────────────
# Move selection
# ──────────────────────────────────────

def choose_player_move(player, enemy):
    """Display move menu and return a Move object, 'item', or 'run'."""
    available = get_available_moves(player)

    print("  MOVES:")
    for i, key in enumerate(available, 1):
        move = PLAYER_MOVES[key]
        if move.power > 0:
            type_mult = TYPE_CHART[move.move_type][enemy.enemy_type]
            if type_mult == 2.0:
                eff = " ◆ SUPER EFFECTIVE"
            elif type_mult == 0.5:
                eff = " ◇ not very effective"
            else:
                eff = ""
            print(f"  [{i}] {move.name:<20} {move.move_type:<8} | Pwr {move.power} | "
                  f"Acc {int(move.accuracy * 100)}% | {move.description}{eff}")
        else:
            print(f"  [{i}] {move.name:<20} {move.move_type:<8} | {move.description}")

    item_n = len(available) + 1
    run_n  = item_n + 1
    print(f"  [{item_n}] Use Item")
    print(f"  [{run_n}] Run")
    print()

    while True:
        try:
            raw = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit()
        if raw.isdigit():
            c = int(raw)
            if 1 <= c <= len(available):
                return PLAYER_MOVES[available[c - 1]]
            if c == item_n:
                return 'item'
            if c == run_n:
                return 'run'
        print("  Choose a valid number.")


def choose_enemy_move(enemy):
    """Select an enemy move. Returns None if suppressed."""
    if 'suppressed' in enemy.statuses:
        return None
    # Boss uses Lunge (priority=2) when below 30% HP
    if enemy.is_boss and enemy.hp < enemy.max_hp * 0.30:
        for m in enemy.moves:
            if m.name == 'Lunge':
                return m
    return random.choice(enemy.moves)


# ──────────────────────────────────────
# Move resolution
# ──────────────────────────────────────

def resolve_player_move(player, enemy, move):
    """Apply player's chosen move to the enemy."""
    # Accuracy check (blinded reduces acc by 40%)
    acc = move.accuracy * (0.60 if 'blinded' in player.combat_statuses else 1.0)
    if random.random() > acc:
        print(f"  Your {move.name} missed!")
        return

    type_mult = TYPE_CHART[move.move_type][enemy.enemy_type]

    # Guard — defensive buff on self
    if move.effect == 'steadied' and move.power == 0:
        player.combat_statuses['steadied'] = 1
        print("  You take a defensive stance. Next hit reduced by 40%.")
        return

    # Override — suppress enemy
    if move.effect == 'suppressed' and move.power == 0:
        if random.random() <= move.effect_chance:
            enemy.statuses['suppressed'] = 1
            print(f"  You override {enemy.name}'s next action — it freezes.")
        else:
            print(f"  Override failed. {enemy.name} resists.")
        return

    # Damage moves
    if move.power > 0:
        # Stressed player deals 75% damage
        atk = int(player.combat_attack * 0.75) if 'stressed' in player.combat_statuses else player.combat_attack
        damage = calc_damage(atk, move.power, enemy.defense, type_mult)

        # Enemy's guard reduces incoming damage
        if enemy.guarded:
            damage = int(damage * 0.60)
            enemy.guarded = False

        enemy.hp = max(0, enemy.hp - damage)

        eff = ""
        if type_mult == 2.0:
            eff = " Super effective!"
        elif type_mult == 0.5:
            eff = " Not very effective..."

        print(f"  {move.name} hits for {damage} damage.{eff}")

        # Secondary status effect on enemy
        if move.effect and move.effect != 'steadied' and random.random() <= move.effect_chance:
            if move.effect not in enemy.statuses:
                enemy.statuses[move.effect] = 3
                print(f"  {enemy.name} is now {move.effect}!")


def resolve_enemy_move(player, enemy, move):
    """Apply enemy's chosen move to the player."""
    if move is None:
        # Suppressed — skip turn and decrement
        print(f"  {enemy.name} hesitates — suppressed!")
        enemy.statuses['suppressed'] = max(0, enemy.statuses.get('suppressed', 1) - 1)
        if enemy.statuses['suppressed'] <= 0:
            del enemy.statuses['suppressed']
        return

    # Blinded enemy has reduced accuracy
    acc = move.accuracy * (0.60 if 'blinded' in enemy.statuses else 1.0)
    if random.random() > acc:
        print(f"  {enemy.name}'s {move.name} missed!")
        return

    type_mult = TYPE_CHART[move.move_type][player.player_type]

    if move.power > 0:
        # Stressed enemy deals 75% damage
        atk = int(enemy.attack * 0.75) if 'stressed' in enemy.statuses else enemy.attack
        damage = calc_damage(atk, move.power, player.combat_defense, type_mult)

        # Player's steadied status reduces damage
        if 'steadied' in player.combat_statuses:
            damage = int(damage * 0.60)
            del player.combat_statuses['steadied']
            print("  Your guard absorbs some of the impact.")

        player.hp = max(0, player.hp - damage)

        eff = ""
        if type_mult == 2.0:
            eff = " Super effective!"
        elif type_mult == 0.5:
            eff = " Not very effective..."

        print(f"  {enemy.name} uses {move.name} — {damage} damage to you!{eff}")

        # Status effect on player
        if move.effect and random.random() <= move.effect_chance:
            if move.effect not in player.combat_statuses:
                player.combat_statuses[move.effect] = 3
                print(f"  You are {move.effect}!")


# ──────────────────────────────────────
# Status tick & item use
# ──────────────────────────────────────

def process_status_tick(player, enemy):
    """Tick down status durations and apply DoT effects."""
    # --- Player statuses ---
    if 'infected' in player.combat_statuses:
        player.hp = max(0, player.hp - 3)
        player.combat_statuses['infected'] -= 1
        if player.combat_statuses['infected'] <= 0:
            del player.combat_statuses['infected']
            print("  The infection clears.")
        else:
            print(f"  Infected: −3 HP.")

    for s in list(player.combat_statuses.keys()):
        if s == 'infected':
            continue
        player.combat_statuses[s] -= 1
        if player.combat_statuses[s] <= 0:
            del player.combat_statuses[s]

    # --- Enemy statuses ---
    if 'infected' in enemy.statuses:
        enemy.hp = max(0, enemy.hp - 3)
        enemy.statuses['infected'] -= 1
        if enemy.statuses['infected'] <= 0:
            del enemy.statuses['infected']

    for s in list(enemy.statuses.keys()):
        if s in ('infected', 'suppressed'):
            continue
        enemy.statuses[s] -= 1
        if enemy.statuses[s] <= 0:
            del enemy.statuses[s]
            if s == 'blinded':
                print(f"  {enemy.name} recovers from blindness.")
            elif s == 'stressed':
                print(f"  {enemy.name}'s stress fades.")


def use_item_in_combat(player):
    """Use a consumable item during combat. Returns True if item was used."""
    usable = []
    if player.has_item('first aid kit'):
        usable.append(('first aid kit', 'Restore 20 HP'))
    for food in ('food supplies', 'energy bars'):
        if player.has_item(food):
            usable.append((food, 'Restore 10 HP'))
            break
    for water in ('water bottle', 'bottled water'):
        if player.has_item(water):
            usable.append((water, 'Restore 5 HP, reduces stress'))
            break

    if not usable:
        print("  No usable items.")
        return False

    print("  ITEMS:")
    for i, (item, desc) in enumerate(usable, 1):
        print(f"  [{i}] {item} — {desc}")
    print("  [0] Cancel")
    print()

    while True:
        try:
            raw = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            return False
        if raw == '0':
            return False
        if raw.isdigit():
            c = int(raw)
            if 1 <= c <= len(usable):
                item_name, _ = usable[c - 1]
                if item_name == 'first aid kit':
                    heal = min(20, player.max_hp - player.hp)
                    player.hp += heal
                    print(f"  You apply the first aid kit. +{heal} HP.")
                    player.remove_item('first aid kit')
                elif 'food' in item_name or 'bar' in item_name or 'bars' in item_name:
                    heal = min(10, player.max_hp - player.hp)
                    player.hp += heal
                    print(f"  You eat. +{heal} HP.")
                    player.remove_item(item_name)
                else:
                    heal = min(5, player.max_hp - player.hp)
                    player.hp += heal
                    player.survival['stress'] = max(0, player.survival['stress'] - 10)
                    print(f"  You drink. +{heal} HP.")
                    player.remove_item(item_name)
                return True
        print("  Choose a valid number.")


# ──────────────────────────────────────
# Main combat loop
# ──────────────────────────────────────

def combat_loop(player, enemy):
    """
    Run a full combat encounter.
    Returns: 'win', 'lose', or 'escaped'.
    """
    while True:
        # ── End conditions ──
        if enemy.hp <= 0:
            separator()
            slow_print(f"  {enemy.name} goes down.")
            time.sleep(0.3)
            return 'win'

        if player.hp <= 0:
            return 'lose'

        # ── Show battle state ──
        display_battle_status(player, enemy)

        # ── Player action ──
        action = choose_player_move(player, enemy)
        print()

        # ── Run ──
        if action == 'run':
            if not enemy.is_boss and random.random() < 0.70:
                slow_print("  You slip back into the shadows.")
                return 'escaped'
            elif not enemy.is_boss:
                slow_print(f"  You couldn't get away — {enemy.name} cuts you off!")
            else:
                slow_print(f"  {enemy.name} blocks every exit. There's no running.")
            # Enemy still attacks on failed run
            emove = choose_enemy_move(enemy)
            resolve_enemy_move(player, enemy, emove)
            print()
            process_status_tick(player, enemy)
            continue

        # ── Use Item ──
        if action == 'item':
            used = use_item_in_combat(player)
            if not used:
                continue  # cancelled — don't advance turn
            # Enemy attacks while you rummage
            emove = choose_enemy_move(enemy)
            print()
            resolve_enemy_move(player, enemy, emove)
            print()
            process_status_tick(player, enemy)
            continue

        # ── Regular move ──
        emove = choose_enemy_move(enemy)

        # Turn order: priority first, then speed
        player_speed    = player.core_stats['Agility']
        player_priority = action.priority
        enemy_priority  = emove.priority if emove else 0

        if enemy_priority > player_priority:
            # Enemy goes first (e.g. Barbados Lunge)
            resolve_enemy_move(player, enemy, emove)
            if player.hp > 0:
                resolve_player_move(player, enemy, action)
        else:
            # Player goes first
            resolve_player_move(player, enemy, action)
            if enemy.hp > 0:
                resolve_enemy_move(player, enemy, emove)

        print()
        process_status_tick(player, enemy)


# ============================================================
# READABLE DOCUMENTS
# ============================================================

DOCUMENTS = {
    "mel's notebook": {
        "title": "Mel's Notebook — Final Entry",
        "text": (
            "The handwriting is shaky, rushed.\n\n"
            "  'March 16th — The compound is breaking down faster than\n"
            "  anticipated. Barbados' condition is deteriorating rapidly.\n"
            "  He still believes he can reverse it. He can't.\n\n"
            "  He's becoming aggressive. Unpredictable.\n\n"
            "  If anyone finds this — do not approach him.\n"
            "  Barbados isn't human anymore.\n\n"
            "  I was wrong to stay. I should have—'\n\n"
            "The entry cuts off. The rest of the page is blank."
        )
    },
    "research log": {
        "title": "Partially Burned Research Log",
        "text": (
            "The edges of every page are charred.\n\n"
            "  'Subject 01 — stable. Alive. Neural activity fluctuating\n"
            "  beyond expected parameters. The compound is doing something\n"
            "  we didn't anticipate. Subject is different.\n\n"
            "  Subject 02 — A. Barbados. Self-administered high-dose.\n"
            "  Results: catastrophic.\n\n"
            "  The prototype was never meant for—'\n\n"
            "The final entry is violently scribbled out.\n"
            "Underneath: 'I'm sorry.'"
        )
    },
    "elias's diary page": {
        "title": "Elias March — Diary Page",
        "text": (
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
            "A bloodstained letter, placed deliberately in the floor.\n\n"
            "  'If you're reading this, you made it further than I did.\n\n"
            "  Don't go to the quarantine room. Whatever is in that room\n"
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
            "Static. Then a voice — strained.\n\n"
            "  'This is Daniel. Daniel Everett. Lab assistant.\n"
            "  If you found this, Barbados is already gone.\n"
            "  Don't try to understand what he became — just run.\n\n"
            "  He started on me first. Said it was a lab accident.\n"
            "  But I saw his notes. I was always the first test.\n\n"
            "  I tried to destroy the samples. Too late.\n\n"
            "  Whatever you are now... fight it. Stay human.'\n\n"
            "The recording cuts to silence."
        )
    },
    "kristy's journal": {
        "title": "Kristy O'Hara — Personal Journal",
        "text": (
            "Leather-bound. Hidden under the mattress.\n\n"
            "  'Week 3 — I keep telling myself there's a line he won't cross.\n\n"
            "  Week 5 — Barbados let in three more survivors today. Infected.\n"
            "  He called them willing participants. They weren't willing.\n\n"
            "  Week 7 — Mel is dead. I got Barbados into the quarantine room.\n"
            "  I don't know how. Adrenaline. Terror. Something else.\n\n"
            "  Week 8 — The scratching stopped for two days. I thought it was\n"
            "  over. Then it started again. Slower. Deliberate.\n"
            "  He's not trying to escape. He's practicing.\n\n"
            "  I'm not going to make it out of here. But maybe someone will.\n"
            "  The key is in the study. God help whoever uses it.'"
        )
    },
    "medical file": {
        "title": "Patient File — Subject 01 (Classified)",
        "text": (
            "Red tape tears easily. Inside: a photograph — you.\n"
            "A different version. Before.\n\n"
            "  'Subject 01 — Davon Gass.\n"
            "  Admitted: Week 1.\n"
            "  Diagnosis: [REDACTED]\n"
            "  Treatment: Barbados Compound, high-dose.\n\n"
            "  Week 3 — Accelerated recovery. Anomalous strength readings.\n"
            "  Elevated neural response.\n\n"
            "  Week 6 — No longer responding to standard pain stimuli.\n"
            "  Dr. Barbados: 'Subject 01 is different. Keep monitoring.'\n\n"
            "  Week 7 — Placed in induced sleep. For observation.\n"
            "  'He must not wake until I understand what he is becoming.\n"
            "   Or what I have created.'\n\n"
            "  Week 8 — [NO FURTHER ENTRIES]'\n\n"
            "You are Subject 01.\n"
            "You have been asleep for eight weeks.\n"
            "You have been becoming something since the beginning."
        )
    },
    "sample case": {
        "title": "Sample Container — Subject 01 Baseline",
        "text": (
            "  'Subject 01 — Pre-compound baseline.\n"
            "  Post-compound deviation: +340% neural sensitivity.\n"
            "  Compound absorption: complete. Irreversible.\n\n"
            "  Note: Subject 01 carries no zombie aggression markers.\n"
            "  The compound adapted to him, not the other way around.\n"
            "  He is not infected. He is something new entirely.\n\n"
            "  This is the result we were looking for.\n"
            "  This is what we were afraid of.'\n\n"
            "The case is empty. Whatever was inside it broke out.\n"
            "Or walked away on its own."
        )
    },
    "survivor note": {
        "title": "Survivor Note — Thomas Halley",
        "text": (
            "Scrawled on the back of a takeout receipt. Barely legible.\n\n"
            "  'I don't know who will find this. I don't know if anyone will.\n\n"
            "   My name is Thomas. I was a delivery driver. I came here three\n"
            "   weeks ago looking for shelter after everything went wrong.\n"
            "   Barbados was already gone by then — locked up, they said.\n\n"
            "   I sat in this chair for two days. Too afraid to move.\n"
            "   Four of us came in. The others didn't make it past night one.\n\n"
            "   I heard them come through the kitchen. Then the study.\n"
            "   They're all through the house now.\n\n"
            "   If you can read this, you're already further than I got.\n"
            "   The lab in the basement — there might be something there.\n"
            "   I never made it that far.\n\n"
            "   Don't sit down like I did. Don't stop.\n"
            "   — Thomas H.'"
        )
    },
}


# ============================================================
# TIMED AMBIENT EVENTS
# ============================================================

TIMED_EVENTS = [
    (5,  "Somewhere above you, something shifts — a single heavy step.\nThen stillness.",
     None, None),
    (10, "The lights stutter — one quick pulse of darkness. Your pulse spikes with them.",
     None, None),
    (15, "Through the walls — slow. Rhythmic. Scratching.\nFrom somewhere west. Measured. Patient.",
     None, 'heard_scratching'),
    (20, "The walkie-talkie crackles once.\nStatic. A voice, barely audible:\n"
         "  '— anyone? If you can hear this —'\nIt cuts out before you can respond.",
     'walkie-talkie', 'heard_first_signal'),
    (28, "A sound from outside. Far away — glass breaking.\nThen nothing.",
     None, None),
    (38, "The walkie-talkie comes alive. Clearer.\nA woman's voice — controlled:\n"
         "  'We have a camp. Northwest of the city. Frequency 7.4.\n"
         "   Don't come alone. Don't come infected.'\n"
         "The transmission repeats twice, then cuts.\n(Type RADIO to respond.)",
     'walkie-talkie', 'heard_maya_broadcast'),
    (50, "The scratching from the west has stopped.\nSomehow that's worse.",
     None, None),
]

_fired_events = set()

def check_timed_events(player):
    global _fired_events
    for (turn_thresh, message, req_item, flag) in TIMED_EVENTS:
        if player.turns >= turn_thresh and turn_thresh not in _fired_events:
            if req_item and not player.has_item(req_item):
                continue
            _fired_events.add(turn_thresh)
            print()
            separator()
            slow_print(message)
            separator()
            if flag:
                player.story_flags[flag] = True
            if flag == 'heard_maya_broadcast':
                player.add_note('people',
                    "Maya — survivor running a camp ~4km northwest. Frequency 7.4.")


# ============================================================
# DYNAMIC ROOM DESCRIPTIONS
# ============================================================

def get_room_description(room_name, rooms, player):
    base   = rooms[room_name]['description']
    flags  = player.story_flags
    addons = []

    if room_name == 'Basement':
        if 'generator_started' in flags:
            addons.append(
                "The generator hums in the alcove. The card reader on the\n"
                "east lab door glows green — it's powered now."
            )
    elif room_name == 'Entrance Hall':
        if 'quarantine_opened' in flags:
            addons.append(
                "The smell from the quarantine room drifts through from the living room."
            )
        if 'knows_protagonist_is_subject_01' in flags:
            addons.append(
                "The scratch marks at the base of the front door catch your eye.\n"
                "Were any of them like you?"
            )
    elif room_name == 'Living Room':
        if 'found_kristys_warning' in flags and 'quarantine_opened' not in flags:
            addons.append(
                "Kristy said the key was in the study.\n"
                "The quarantine door to the west feels like a countdown."
            )
        if 'quarantine_opened' in flags:
            addons.append(
                "The quarantine door stands open to the west.\n"
                "The smell from inside reaches you here."
            )
    elif room_name == 'Study':
        if ('knows_about_compound' in flags and
                'found_mels_warning' in flags and
                'heard_daniels_warning' in flags):
            addons.append(
                "You've read enough to understand what happened here.\n"
                "What was done. What you are."
            )
    elif room_name == 'Master Bedroom':
        if 'bathroom_zombie_mercy' in flags:
            addons.append(
                "The bathroom is silent now. You did what had to be done."
            )
        if 'read_full_journal' in flags:
            addons.append(
                "You understand now why Kristy stayed as long as she did."
            )
    elif room_name == 'Bathroom':
        if 'bathroom_zombie_mercy' in flags:
            addons.append(
                "The figure is gone. The bathtub has a stain it didn't have before."
            )
        elif 'bathroom_zombie_left' in flags:
            addons.append(
                "It's still there. Still watching the door."
            )
    elif room_name == 'Lab Wing':
        if 'read_medical_file' in flags:
            addons.append(
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
            'exits':        {'north': 'Entrance Hall'},
            'locked_exits': {'east': 'Lab Wing'},
            'brief': "Cold steel and chemical rot. You woke up here.",
            'description': (
                "You are in the Basement Lab.\n"
                "The air is thick — stale chemicals, dried blood, something rotten.\n"
                "A cold steel operating table sits in the centre, IV tubes dangling\n"
                "loose. Nearby, an empty suspension tank looms — reinforced glass fogged,\n"
                "dark residue clinging to the inside.\n"
                "A heavy metal door to the east is labelled 'Lab Wing Access' — locked.\n"
                "Stairs lead north toward the rest of the house."
            ),
            'items': {
                "flashlight":         "A heavy-duty flashlight. Batteries still work.",
                "mel's notebook":     "A small blood-smeared notebook. Cover reads 'M. Peoples'.",
                "elias's diary page": "A torn diary page. Bloodstained robe nearby.",
                "research log":       "A partially burned research log.",
            },
            'objects': {
                "operating table": (
                    "Cold steel with restraint marks worn into the sides.\n"
                    "The IV tubes were ripped out, not removed carefully.\n"
                    "Someone left in a hurry. Or was taken."
                ),
                "suspension tank": (
                    "An empty reinforced glass tank — large enough for a person.\n"
                    "Dark residue inside. A discoloured ring on the floor beneath.\n"
                    "Whatever was kept here was removed without being shut down."
                ),
                "blood trail": (
                    "A smear of dried blood leads from the operating table\n"
                    "toward the far wall and disappears into shadow.\n"
                    "Whoever left this — it wasn't long ago."
                ),
                "lab door": (
                    "Heavy steel. 'Lab Wing Access.'\n"
                    "A card reader on the wall beside it — dark. No power.\n"
                    "The generator could change that."
                ),
                "medical cart": (
                    "Overturned. Scattered syringes. One still has dark,\n"
                    "viscous residue inside. You don't pick it up."
                ),
                "generator": (
                    "A large diesel generator. Fuel gauge: a quarter tank.\n"
                    "A pull cord along the right side, stiff from disuse.\n"
                    "Enough fuel to run. It just needs to be started.\n"
                    "(Try: USE FLASHLIGHT ON GENERATOR, or START GENERATOR)"
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
            'brief': "The front door is barricaded — nailed shut from this side. Not your way out.",
            'description': (
                "You are in the Entrance Hall.\n"
                "A chandelier hangs above — crystals coated in dust and cobwebs.\n"
                "The front doors are barricaded with planks nailed haphazardly.\n"
                "Scratch marks at the base of the doors from the inside.\n"
                "A grand staircase to the right, its railing splintered.\n"
                "Passages lead west to the parlour, east to a cloakroom, north deeper in."
            ),
            'items': {},
            'objects': {
                "front door": (
                    "Heavy wood, barricaded from the inside — thick planks nailed hard.\n"
                    "Scratch marks at the base: deep, ragged. Fingernails.\n"
                    "Something tried to get OUT, not in. They didn't make it.\n\n"
                    "The door is sealed. You'd need a crowbar or something heavy\n"
                    "to pry the planks loose — and that's if you even want to go out there.\n"
                    "Through the gap: still, grey light. Shapes in the distance. Slow ones.\n\n"
                    "This isn't your exit. Not yet."
                ),
                "scratch marks": (
                    "Long ragged gouges at floor level. Multiple sets.\n"
                    "They all faced the same direction — toward the door. Toward outside.\n"
                    "None of them made it."
                ),
                "chandelier": (
                    "Once grand. Several crystals missing. It sways faintly\n"
                    "even though there's no wind you can feel.\n"
                    "The chain looks old."
                ),
                "staircase": (
                    "Wide stairs. One baluster missing, another cracked.\n"
                    "Dried blood on the third step — a smear that trails up and stops."
                ),
                "bloodstain": (
                    "A dark stain near the front door. The shape suggests someone\n"
                    "sat here for a while. Bleeding. Waiting.\n"
                    "Whatever they were waiting for never came."
                ),
            }
        },

        'Parlor': {
            'exits': {'east': 'Entrance Hall'},
            'brief': "Everything preserved under sheets. Like no one dared disturb it.",
            'description': (
                "You are in the Parlor.\n"
                "Antique furniture under dusty white sheets — preserved, undisturbed.\n"
                "A grand mirror above a cold fireplace, cracked diagonally.\n"
                "A broken phonograph in the corner, needle stuck.\n"
                "The air is stale — aged wood and something faintly floral."
            ),
            'items': {
                "guestbook":   "A dust-covered guestbook. Pages brittle.",
                "energy bars": "Three sealed protein bars stashed behind the phonograph. Still good.",
            },
            'objects': {
                "phonograph": (
                    "The needle is stuck in a groove. Someone set it playing\n"
                    "deliberately before they left. You wonder what the last song was."
                ),
                "mirror": (
                    "Cracked diagonally. Your reflection is split — two versions\n"
                    "of you, slightly offset. You look pale. Paler than you should.\n"
                    "You look away before the other one does."
                ),
                "fireplace": (
                    "Cold. Grey ash in the grate. Among the ash, a scrap of\n"
                    "burned paper. One word still legible: 'Shelly.'"
                ),
                "armchair": (
                    "Dried blood on the right armrest. Someone sat here,\n"
                    "injured, and stayed for a while. The indent in the cushion\n"
                    "is still there — deep. They were here for days.\n\n"
                    "Wait. Something is wedged between the cushion and the armrest."
                ),
                "tea set": (
                    "Tipped over. Cups shattered. Whoever left didn't look back.\n"
                    "Tea stains on the tablecloth — long since dry."
                ),
            }
        },

        'Cloakroom': {
            'exits': {'west': 'Entrance Hall'},
            'brief': "Dust-heavy coats. A locked cabinet. One coat missing from the rack.",
            'description': (
                "You are in the Cloakroom.\n"
                "A narrow space lined with coat racks and a storage cabinet.\n"
                "Dust-covered coats hang lifelessly. The floor creaks underfoot.\n"
                "A small mirror on the wall, cracked at one corner."
            ),
            'items': {
                "bottled water": "A sealed bottle tucked deep in a coat pocket. Cold.",
            },
            'objects': {
                "mirror": (
                    "Cracked at the corner. Your reflection is distorted —\n"
                    "one eye lower than the other, jaw at the wrong angle.\n"
                    "You know it's just the crack."
                ),
                "coats": (
                    "Old coats, thick with dust. One rack has a gap —\n"
                    "a coat is missing. The hanger still swings faintly.\n"
                    "House keys in one of the remaining pockets. No use to you."
                ),
                "cabinet": (
                    "A locked wooden cabinet. Basic padlock.\n"
                    "You'd need something thin and rigid to open it."
                ),
                "hat": (
                    "A hat on the floor, brim thick with dust.\n"
                    "It's been there for weeks. The owner didn't come back."
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
            'brief': "Overturned furniture. A letter placed deliberately in the middle of the floor.",
            'description': (
                "You are in the Living Room.\n"
                "A shattered television on its side. An overturned bookcase scattering\n"
                "papers and broken frames across the floor. A photograph on the\n"
                "mantelpiece facing down.\n"
                "A crumpled letter sits in the centre of the floor — placed, not dropped."
            ),
            'items': {
                "kristy's letter": "A bloodstained letter. Placed deliberately.",
            },
            'objects': {
                "photograph": (
                    "Face-down on the mantelpiece. You turn it over:\n"
                    "a man — younger, smiling — with a woman and a small girl.\n"
                    "On the back: 'We'll do this together.'\n"
                    "The man is Dr. Barbados. You don't know how you know that."
                ),
                "quarantine door": (
                    "A heavy reinforced door set into the west wall.\n"
                    "Sliding bolt and keyhole — both engaged.\n"
                    "The wood on the far side is scored with deep, even lines.\n"
                    "Tally marks. You count them before you can stop yourself.\n"
                    "Forty-three."
                ),
                "television": (
                    "Screen caved in — something hit it hard.\n"
                    "A bloodstain on the corner. Plug still in the wall."
                ),
                "bookcase": (
                    "Toppled. Among the papers, a loose research journal page —\n"
                    "equations you don't understand. At the bottom, underlined:\n"
                    "'Do not proceed to Stage 3.'"
                ),
                "mantelpiece": (
                    "Cold stone. The photograph and undisturbed dust.\n"
                    "One small handprint in the dust — too small for an adult."
                ),
            }
        },

        'Kitchen': {
            'exits': {
                'north': 'Living Room',
                'east':  'Study',
            },
            'brief': "Stripped bare. Chemical smell. Don't make sparks.",
            'description': (
                "You are in the Kitchen.\n"
                "The cabinets hang open and empty — stripped.\n"
                "Floorboards near the pantry door have collapsed inward.\n"
                "A faint chemical smell in the air. Not food. Something piped.\n"
                "Be careful with anything that makes a spark."
            ),
            'items': {
                "food supplies": "A dented tin of canned goods and some sealed protein bars.",
                "water bottle":  "A full sealed water bottle.",
            },
            'objects': {
                "cabinets": (
                    "Every shelf emptied. Someone was here before you.\n"
                    "One cabinet door is hanging off its hinge."
                ),
                "floorboards": (
                    "Several boards near the pantry collapsed into a dark space below.\n"
                    "The gap isn't large enough to fit through.\n"
                    "The smell coming up is bad — rot and standing water."
                ),
                "stove": (
                    "Old gas stove. One burner knob turned slightly — not all the way.\n"
                    "That explains the smell. Don't use open flame in this room."
                ),
                "sink": (
                    "Bone dry. Both taps open, nothing coming out.\n"
                    "Dead plant on the windowsill. Through the window: empty garden."
                ),
            }
        },

        'Study': {
            'exits': {'west': 'Kitchen'},
            'brief': "Research notes everywhere. One line pinned to the wall: 'Trust no one.'",
            'description': (
                "You are in the Study.\n"
                "A desk covered in handwritten research notes. Bookshelves\n"
                "lining the walls, one toppled. A dark computer terminal — no power.\n"
                "Pinned to the wall, underlined twice: 'Trust no one.'"
            ),
            'items': {
                "walkie-talkie":  "A military-grade walkie-talkie. Charged. Only static.",
                "quarantine key": "A heavy key on a red lanyard. Labelled 'Q-ROOM'.",
                "voice recorder": "A cracked voice recorder. Indicator light still blinking.",
            },
            'objects': {
                "desk": (
                    "Covered in research notes. Cell diagrams. Equations.\n"
                    "'Stage 2 replication' and 'neural bridge — viable?' throughout.\n"
                    "Last page is blank except four words pressed hard into the paper:\n"
                    "'What have I done.'"
                ),
                "terminal": (
                    "Dark. No power.\n"
                    "Sticky note on screen: 'Camera log — 3 entries. Remote access required.'\n"
                    "If the generator were running, you might access it."
                ),
                "bookshelves": (
                    "Medical and biology texts. One shelf swept completely clear.\n"
                    "In the gap, scratched into the wood: 'RUN'"
                ),
                "research notes": (
                    "Dozens of loose pages. Neural pathways. Toxicology.\n"
                    "Then a shift — infection vectors. Reanimation timelines.\n"
                    "The handwriting gets messier toward the end.\n"
                    "The final few pages are written in something that isn't ink."
                ),
                "safe": (
                    "A small wall safe behind a pulled-aside shelf.\n"
                    "Combination lock. You'd need the combination."
                ),
            }
        },

        'Master Bedroom': {
            'exits': {
                'south': 'Living Room',
                'east':  'Bathroom',
            },
            'brief': "Torn sheets. A handprint smeared down the wall. Empty pill bottles.",
            'description': (
                "You are in the Master Bedroom.\n"
                "A large bed with torn sheets, half-pulled to the floor.\n"
                "The closet door hangs ajar. A bloody handprint smeared down the\n"
                "wall beside the window — someone slid. Empty medication bottles\n"
                "on the nightstand. The room smells like something that ended badly."
            ),
            'items': {
                "first aid kit":    "A proper medical kit — sealed. Bandages, antiseptic, sutures.",
                "kristy's journal": "A leather-bound journal. Dried blood on the cover.",
            },
            'objects': {
                "bloody handprint": (
                    "A single handprint on the wall, smeared downward.\n"
                    "The print is small. A woman's hand."
                ),
                "closet": (
                    "Inside: clothes on hangers, shoes on the floor, a scarf\n"
                    "torn cleanly in half. Nothing missing except who wore these."
                ),
                "nightstand": (
                    "Three empty pill bottles — prescribed to 'K. O'Hara.'\n"
                    "Anxiety. Insomnia. And a third label you don't recognise.\n"
                    "All empty. Finished, not spilled."
                ),
                "window": (
                    "Cracked. Curtains drawn but light bleeds through.\n"
                    "Through it: the overgrown garden, and shapes beyond.\n"
                    "Slow. Aimless. More than you can count.\n"
                    "They haven't noticed the house yet."
                ),
            }
        },

        'Bathroom': {
            'exits': {'west': 'Master Bedroom'},
            'brief': "A figure in a hospital gown, slumped against the bathtub. Not quite still.",
            'description': (
                "You are in the Bathroom.\n"
                "A cracked mirror above a dry sink. Stained tiles.\n"
                "A figure in a hospital gown is slumped against the bathtub.\n"
                "The smell is very bad. Move carefully."
            ),
            'items': {},
            'objects': {
                "mirror": (
                    "Cracked in several places. Your reflection fragments across\n"
                    "the breaks — pale, hollow, fractured.\n"
                    "One reflection doesn't quite line up with the others.\n"
                    "You tell yourself it's the angle."
                ),
                "figure": (
                    "A zombie. Former patient — hospital gown, bare feet, IV port still taped\n"
                    "to its arm. It stirs when you get close. Not aggressive yet.\n"
                    "But it will be if you make noise.\n"
                    "It was a person once. Not long ago.\n"
                    "(EXAMINE FIGURE to engage.)"
                ),
                "sink": (
                    "Bone dry. Tap rusted open, nothing coming out.\n"
                    "A ring of grime where water used to reach."
                ),
                "medicine cabinet": (
                    "Above the sink, door hanging open.\n"
                    "Empty — mostly. One unused syringe still in packaging.\n"
                    "You leave it."
                ),
                "bathtub": (
                    "Dry. A dark ring marks the old waterline.\n"
                    "The bottom is stained in a way that wasn't just water."
                ),
            }
        },

        'Quarantine Room': {
            'exits': {'east': 'Living Room'},
            'brief': "Tally marks cover every wall. Something breathes in the dark.",
            'description': (
                "You are in the Quarantine Room.\n"
                "The walls are covered in long, deliberate scratch marks — measured,\n"
                "evenly spaced. Tally marks. The decay smell is overwhelming.\n"
                "The room is dark beyond what your flashlight reaches.\n"
                "You can hear breathing. Slow. Patient."
            ),
            'items': {},
            'objects': {
                "scratch marks": (
                    "Rows of parallel lines etched deep into the plaster.\n"
                    "You count them. You stop counting.\n"
                    "You don't want to know how long he's been in here."
                ),
                "darkness": (
                    "The corners are absolute black.\n"
                    "You can't see what's there.\n"
                    "But you can hear it breathing."
                ),
                "barbados": (
                    "He's here. Still — until he isn't.\n"
                    "His eyes catch your light: pale, luminous, aware.\n"
                    "He turns toward you slowly. All the time in the world.\n"
                    "Like someone who has been waiting specifically for you.\n"
                    "He knows you're here. He knew before you opened the door."
                ),
            }
        },

        'Lab Wing': {
            'exits': {'west': 'Basement'},
            'brief': "Secondary lab. A workstation glows. The specimen case was broken from inside.",
            'description': (
                "You are in the Lab Wing.\n"
                "A secondary research space — clinical, smaller than the basement.\n"
                "Steel cabinets line the walls. A workstation glows on backup power.\n"
                "A glass specimen case on the central table — broken open from inside.\n"
                "The air is colder here. Wrong cold."
            ),
            'items': {
                "medical file": "A sealed file, red-taped. Your name is on the outside.",
                "sample case":  "A cracked specimen container. 'Subject 01 — Baseline.'",
            },
            'objects': {
                "workstation": (
                    "Terminal on backup power. Screen shows a log entry:\n"
                    "  'Subject 01 — status: AWOL.\n"
                    "   Last reading: off-chart neural activity.\n"
                    "   Recommend immediate containment if located.'\n"
                    "A camera feed: four rooms. Three dark. One isn't.\n"
                    "The Quarantine Room. Something moves in the corner."
                ),
                "specimen case": (
                    "Reinforced glass — designed to hold biohazardous material.\n"
                    "Something broke out. The edges are pushed outward.\n"
                    "Bloodstains on the table. Old ones and new ones.\n"
                    "Label: 'Subject 01 — Baseline Sample.'"
                ),
                "cabinets": (
                    "Most sealed with biohazard locks. One stands open — emptied.\n"
                    "On the shelf inside, scratched into the metal:\n"
                    "'He knows you're coming.'"
                ),
                "camera feed": (
                    "Four split-screen feeds. Three dark.\n"
                    "Quarantine Room: something in the corner. Not moving.\n"
                    "Waiting. The timestamp reads 8 weeks ago. Looping."
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

    if text in ('i', 'inv', 'inventory'):           return ('inventory', None)
    if text in ('stats', 'status'):                  return ('stats', None)
    if text in ('help', 'instructions', '?'):        return ('help', None)
    if text in ('look', 'l', 'look around'):         return ('look', None)
    if text in ('quit', 'exit', 'q'):                return ('quit', None)
    if text in ('notes', 'codex', 'journal', 'log'): return ('notes', None)
    if text in ('map', 'layout', 'floorplan'):       return ('map', None)
    if text in ('hint', 'hints'):                    return ('hint', None)
    if text in ('radio', 'respond', 'broadcast',
                'call out', 'transmit', 'answer radio'): return ('radio', None)

    words = text.split()
    verb  = words[0]
    rest  = ' '.join(words[1:]) if len(words) > 1 else ''

    if verb in ('north', 'south', 'east', 'west'):
        return ('go', verb)
    if verb in ('n', 's', 'e', 'w'):
        return ('go', {'n':'north','s':'south','e':'east','w':'west'}[verb])

    if verb in ('go', 'walk', 'move', 'head', 'travel', 'run'):
        dir_map = {
            'n':'north','north':'north',
            's':'south','south':'south',
            'e':'east', 'east': 'east',
            'w':'west', 'west': 'west',
        }
        dir_word = rest.split()[0] if rest else ''
        return ('go', dir_map.get(dir_word, dir_word))

    if verb in ('peek', 'look into', 'glance'):
        dir_map = {
            'n':'north','north':'north',
            's':'south','south':'south',
            'e':'east', 'east': 'east',
            'w':'west', 'west': 'west',
        }
        dir_word = rest.split()[0] if rest else ''
        return ('peek', dir_map.get(dir_word, dir_word))

    if verb in ('examine', 'look', 'inspect', 'check', 'search', 'study'):
        target = rest
        if rest.startswith('at '):
            target = rest[3:]
        if target and target not in ('around', 'room', 'here', ''):
            return ('examine', target)
        return ('look', None)

    if verb == 'read':
        return ('read', rest)

    if verb in ('get', 'take', 'grab', 'pick', 'collect', 'retrieve'):
        if rest.startswith('up '):
            rest = rest[3:]
        return ('get', rest)

    if verb in ('drop', 'discard', 'leave', 'put down'):
        return ('drop', rest)

    if verb == 'use':
        if ' on ' in rest:
            parts = rest.split(' on ', 1)
            return ('use', (parts[0].strip(), parts[1].strip()))
        return ('use', (rest, None))

    if verb == 'open':
        return ('open', rest)

    if verb in ('eat', 'consume'):  return ('eat', rest)
    if verb == 'drink':             return ('drink', rest)

    if verb == 'unlock':
        return ('use', (rest, 'door'))

    if verb in ('start', 'pull', 'activate', 'crank', 'yank'):
        return ('start', rest if rest else 'generator')

    if verb in ('radio', 'respond', 'broadcast', 'transmit'):
        return ('radio', rest)

    return ('unknown', text)


# ============================================================
# ACTIONS
# ============================================================

def action_enter_room(room_name, rooms, player):
    """Shows brief description on room entry. Full description on LOOK."""
    room = rooms[room_name]
    separator()
    print(room_name.upper())
    print(room.get('brief', ''))
    print()

    all_exits = list(room.get('exits', {}).keys())
    locked    = [f"{d} (locked)" for d in room.get('locked_exits', {}).keys()]
    if all_exits or locked:
        print("Exits: " + ", ".join(all_exits + locked) + ".")

    if room.get('items'):
        item_names = list(room['items'].keys())
        if len(item_names) == 1:
            print(f"You notice: a {item_names[0]}.")
        else:
            print("You notice: " + ", ".join(f"a {i}" for i in item_names) + ".")

    separator()


def action_look(room_name, rooms, player):
    """Full room description — shown on LOOK command."""
    room = rooms[room_name]
    separator()
    print(room_name.upper())
    print()
    fast_print(get_room_description(room_name, rooms, player))

    if room.get('items'):
        print()
        item_names = list(room['items'].keys())
        if len(item_names) == 1:
            fast_print(f"You notice a {item_names[0]} here.")
        else:
            fast_print("You notice: " + ", ".join(f"a {i}" for i in item_names) + ".")

    all_exits = list(room.get('exits', {}).keys())
    locked    = [f"{d} (locked)" for d in room.get('locked_exits', {}).keys()]
    if all_exits or locked:
        fast_print("Exits: " + ", ".join(all_exits + locked) + ".")

    separator()


def action_peek(direction, room_name, rooms, player):
    """Peek into adjacent room without moving."""
    if not direction:
        print("Peek which direction? (north, south, east, west)")
        return

    room   = rooms[room_name]
    exits  = room.get('exits', {})
    locked = room.get('locked_exits', {})

    if direction in exits:
        dest      = exits[direction]
        dest_room = rooms[dest]
        separator()
        print(f"Looking {direction}:")
        print(f"  {dest.upper()}")
        print(f"  {dest_room.get('brief', '')}")
        separator()
    elif direction in locked:
        dest = locked[direction]
        separator()
        print(f"Looking {direction}: {dest.upper()} — locked.")
        if dest == 'Quarantine Room':
            print("  You can hear something on the other side. Slow. Deliberate.")
        elif dest == 'Lab Wing':
            print("  The card reader is dark. No power.")
        separator()
    else:
        print(f"There's nothing to the {direction}.")


def action_examine(target, room_name, rooms, player):
    room = rooms[room_name]

    # V5: Bathroom zombie → combat encounter
    if room_name == 'Bathroom' and target in ('figure', 'zombie', 'person', 'body'):
        if 'bathroom_zombie_resolved' not in player.story_flags:
            _bathroom_zombie_encounter(room_name, rooms, player)
            return
        else:
            separator()
            if 'bathroom_zombie_mercy' in player.story_flags:
                print("There's nothing left to see here.\nWhat you did was necessary. You keep telling yourself that.")
            else:
                print("It's still there. Still watching you from the floor.\nIt hasn't moved toward you. But it hasn't looked away either.")
            separator()
            return

    # V6: Parlor armchair — hidden survivor note discovery
    if room_name == 'Parlor' and target in ('armchair', 'chair', 'cushion'):
        if 'armchair_searched' not in player.story_flags:
            player.story_flags['armchair_searched'] = True
            separator()
            fast_print(rooms['Parlor']['objects']['armchair'])
            print()
            slow_print("You reach into the gap — and pull out a folded piece of paper.")
            slow_print("Someone hid this deliberately.")
            rooms['Parlor']['items']['survivor note'] = "A folded note, tucked in the armchair cushion."
            player.add_note('clues',
                "Found a survivor note in the Parlor armchair — Thomas Halley made it further than most.")
            separator()
            return
        else:
            separator()
            fast_print(rooms['Parlor']['objects']['armchair'])
            separator()
            return

    # V6: Master Bedroom closet — burst zombie
    if room_name == 'Master Bedroom' and target in ('closet',):
        if 'closet_zombie_resolved' not in player.story_flags:
            _closet_zombie_encounter(player, rooms)
            return
        else:
            separator()
            print("The closet is empty now. Everything still on the hangers.")
            separator()
            return

    # V6: Front door — clear messaging
    if room_name == 'Entrance Hall' and target in ('front door', 'door', 'barricade', 'planks'):
        separator()
        fast_print(rooms['Entrance Hall']['objects']['front door'])
        separator()
        return

    # Generator interaction
    if target in ('generator',) and room_name == 'Basement':
        separator()
        if 'generator_started' in player.story_flags:
            print("The generator runs steadily. The lab door to the east is powered.")
        else:
            print(rooms['Basement']['objects']['generator'])
        separator()
        player.examined.add(target)
        return

    player.examined.add(target)

    for obj_name, obj_desc in room.get('objects', {}).items():
        if target in obj_name or obj_name in target:
            separator()
            fast_print(obj_desc)
            separator()
            return

    for item_name, item_desc in room.get('items', {}).items():
        if target in item_name or item_name in target:
            separator()
            fast_print(item_desc)
            if item_name.lower() in DOCUMENTS:
                print(f"\n(You can READ the {item_name} — pick it up with GET, or read it here.)")
            else:
                print(f"\n(Type GET {item_name} to pick it up.)")
            separator()
            return

    for item in player.inventory:
        if target in item.lower() or item.lower() in target:
            separator()
            if item.lower() in DOCUMENTS:
                print(f"A {item}. You could READ it.")
            else:
                print(f"You examine the {item}. It seems useful — hold onto it.")
            separator()
            return

    print(f"You don't see anything called '{target}' here.")


def action_read(target, room_name, rooms, player):
    """Read documents — works in inventory OR in the room (no pickup required)."""

    def _do_read(item_name):
        doc = DOCUMENTS[item_name.lower()]
        separator()
        slow_print(f"[ {doc['title']} ]")
        print()
        slow_print(doc['text'])
        separator()
        if item_name.lower() not in player.read_documents:
            player.read_documents.append(item_name.lower())
            _on_read(item_name.lower(), player)

    for item in player.inventory:
        if target in item.lower() or item.lower() in target:
            if item.lower() in DOCUMENTS:
                _do_read(item)
                return
            else:
                print(f"There's nothing to read on the {item}.")
                return

    for item_name in rooms[room_name].get('items', {}).keys():
        if target in item_name or item_name in target:
            if item_name.lower() in DOCUMENTS:
                _do_read(item_name)
                return
            else:
                print(f"There's nothing to read on the {item_name}.")
                return

    print(f"You don't see a '{target}' to read.")


def _on_read(doc_name, player):
    """Story flags and hidden stat shifts triggered by reading documents."""
    if doc_name == "mel's notebook":
        player.story_flags['found_mels_warning'] = True
        player.hidden_stats['Mental Stability'] -= 1
        player.add_note('people',
            "Dr. Mel Peoples (Mel) — left a warning: Barbados is no longer human. He didn't make it out.")

    if doc_name == "research log":
        player.story_flags['knows_about_compound']             = True
        player.story_flags['knows_protagonist_is_subject_01']  = True
        slow_print("\n[Something about 'Subject 01' hits differently.]")
        player.add_note('clues',
            "The research log mentions 'Subject 01 — stable, alive, different.' You may be Subject 01.")
        player.add_note('people',
            "Dr. Andre Barbados — self-administered the compound (Subject 02). Results: catastrophic.")

    if doc_name == "elias's diary page":
        player.story_flags['knows_barbados_self_injected'] = True
        player.add_note('people',
            "Elias March — Patient #1. Came for terminal cancer treatment. Sensed something was wrong.")

    if doc_name == "kristy's letter":
        player.story_flags['found_kristys_warning'] = True
        player.story_flags['knows_key_in_study']    = True
        player.add_note('people',
            "Dr. Kristy O'Hara (Kristy) — locked Barbados in the quarantine room. Didn't make it out.")
        player.add_note('clues',
            "The quarantine key is in the study.")

    if doc_name == "voice recorder":
        player.story_flags['heard_daniels_warning'] = True
        player.hidden_stats['Alpha Awareness']      += 1
        player.add_note('people',
            "Daniel Everett — lab assistant. Tried to destroy the compound samples. Failed.")

    if doc_name == "kristy's journal":
        player.story_flags['read_full_journal']     = True
        player.hidden_stats['Alpha Awareness']      += 2
        player.add_note('clues',
            "Barbados isn't trying to escape the quarantine room — he's practicing. Learning.")

    if doc_name == "medical file":
        player.story_flags['read_medical_file']     = True
        player.story_flags['knows_full_truth']      = True
        player.hidden_stats['Alpha Awareness']      += 3
        player.hidden_stats['Mental Stability']     = max(0,
            player.hidden_stats['Mental Stability'] - 2)
        slow_print("\n[You understand now. All of it. What was done to you. What you are.]")
        player.add_note('people',
            "YOU — Davon Gass. Subject 01. The compound adapted to you differently. You are not infected.")
        player.add_note('clues',
            "You are not infected. The compound made you something new entirely. Irreversible.")

    if doc_name == "sample case":
        player.story_flags['knows_compound_irreversible'] = True
        player.hidden_stats['Alpha Awareness']            += 1

    if doc_name == "survivor note":
        player.story_flags['found_survivor_note'] = True
        player.add_note('people',
            "Thomas Halley — delivery driver. Sheltered here after the outbreak. Sat in the Parlor armchair. Didn't make it.")
        player.add_note('clues',
            "Thomas mentioned zombies through the kitchen and study — they've spread through the whole house.")


def action_get(target, room_name, rooms, player):
    room = rooms[room_name]
    for item_name in list(room['items'].keys()):
        if target in item_name or item_name in target:
            player.inventory.append(item_name)
            del room['items'][item_name]
            print(f"You pick up the {item_name}.")
            _on_pickup(item_name, player)
            return
    print(f"There's no '{target}' here to pick up.")


def _on_pickup(item_name, player):
    if item_name == "first aid kit":
        if not player.substats['First Aid']['unlocked']:
            player.unlock_substat('First Aid', 1)
            print("[First Aid substat unlocked.]")
    if item_name == "walkie-talkie":
        player.story_flags['has_comms'] = True
        slow_print("It hisses with static. Something is out there on the frequencies.")
        player.add_note('clues',
            "You have a walkie-talkie. Something might be on the frequencies.")
    if item_name == "quarantine key":
        slow_print("Your hand is unsteady as you pick it up.")
        slow_print("You know what this opens.")
    if item_name == "medical file":
        slow_print("Your name is on the outside.")
        slow_print("Your hands go still.")
    if item_name == "flashlight":
        if not player.substats['Awareness']['unlocked']:
            player.unlock_substat('Awareness', 1)
            print("[Awareness substat unlocked.]")
        slow_print("The beam cuts cleanly through the dark.")
        slow_print("[Flash move now available in combat — shine it in their eyes.]")


def action_go(direction, room_name, rooms, player):
    if not direction:
        print("Go where? (north, south, east, west)")
        return room_name

    room   = rooms[room_name]
    exits  = room.get('exits', {})
    locked = room.get('locked_exits', {})

    if direction in exits:
        return exits[direction]

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
                print("The door is locked — bolt and keyhole both engaged.")
                if 'found_kristys_warning' in player.story_flags:
                    print("Kristy's letter said the key is in the study.")
                else:
                    print("You can hear something on the other side. Slow. Deliberate.")
                return room_name

        if target_room == 'Lab Wing':
            if 'generator_started' in player.story_flags:
                slow_print("The card reader glows green. You push the door open.")
                exits[direction] = locked.pop(direction)
                return target_room
            else:
                print("The card reader is dark. No power.")
                print("Get the generator running first.")
                return room_name

    print("You can't go that way.")
    return room_name


def action_use(item, target, room_name, rooms, player):
    item_lower   = item.lower() if item else ''
    target_lower = target.lower() if target else ''

    if not player.has_item(item_lower):
        found = False
        for inv_item in player.inventory:
            if item_lower in inv_item.lower():
                item_lower = inv_item.lower()
                found = True
                break
        if not found:
            print(f"You're not carrying a '{item}'.")
            return

    if 'flashlight' in item_lower and ('generator' in target_lower or not target_lower):
        if room_name != 'Basement':
            print("There's nothing useful to light up here.")
            return
        if 'generator_started' in player.story_flags:
            print("The generator is already running.")
            return
        if 'generator' not in player.examined:
            print("Examine the generator first.")
            return
        _start_generator(player, rooms)
        return

    if 'flashlight' in item_lower:
        print("You click on the flashlight. The beam cuts sharply through the dark.")
        return

    if 'food' in item_lower or 'energy' in item_lower or 'supplies' in item_lower:
        slow_print("You eat. Your body accepts it with something close to relief.")
        player.survival['hunger'] = min(100, player.survival['hunger'] + 35)
        player.hp = min(player.max_hp, player.hp + 10)
        for fname in ('food supplies', 'energy bars', 'energy bar'):
            if player.remove_item(fname):
                break
        return

    if 'water' in item_lower or 'bottle' in item_lower:
        slow_print("You drink. The dryness in your throat eases slightly.")
        player.survival['thirst'] = min(100, player.survival['thirst'] + 40)
        player.hp = min(player.max_hp, player.hp + 5)
        for wname in ('water bottle', 'bottled water'):
            if player.remove_item(wname):
                break
        return

    if 'first aid' in item_lower:
        heal = min(20, player.max_hp - player.hp)
        slow_print(f"You treat your wounds. +{heal} HP.")
        player.hp = min(player.max_hp, player.hp + heal)
        player.survival['stress'] = max(0, player.survival['stress'] - 20)
        return

    if 'quarantine key' in item_lower:
        print("Try going west to use it on the quarantine room door.")
        return

    print(f"You're not sure how to use that" + (f" on {target}." if target else "."))


def action_start(target, room_name, rooms, player):
    if room_name != 'Basement':
        print("There's nothing here to start.")
        return
    if 'generator_started' in player.story_flags:
        print("The generator is already running.")
        return
    if 'generator' not in player.examined:
        print("Examine the generator before trying to start it.")
        return
    if not player.has_item('flashlight'):
        print("You need better light to see the pull cord clearly.\nTry: USE FLASHLIGHT ON GENERATOR")
        return
    _start_generator(player, rooms)


def _start_generator(player, rooms):
    separator()
    slow_print("You brace the flashlight against your shoulder, freeing both hands.")
    time.sleep(0.3)
    slow_print("The pull cord is stiff — weeks of cold have set in.")
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
    slow_print("Lights flicker on across the basement. The card reader on the east\ndoor blinks from red to green.")
    print()
    slow_print("Lab Wing — now accessible.")
    separator()
    player.story_flags['generator_started'] = True
    if not player.substats['Mechanics']['unlocked']:
        player.unlock_substat('Mechanics', 1)
        print("[Mechanics substat unlocked.]")
    basement = rooms['Basement']
    if 'east' in basement.get('locked_exits', {}):
        basement['exits']['east'] = basement['locked_exits'].pop('east')


def action_eat(target, rooms, room_name, player):
    if any(w in target for w in ('food', 'bar', 'energy', 'supplies', 'tin', 'can')):
        action_use('food supplies', None, room_name, rooms, player)
    else:
        print(f"You don't have any '{target}' to eat.")


def action_drink(target, rooms, room_name, player):
    if any(w in target for w in ('water', 'bottle', 'drink')):
        action_use('water bottle', None, room_name, rooms, player)
    else:
        print(f"You don't have any '{target}' to drink.")


def action_drop(target, room_name, rooms, player):
    for item in list(player.inventory):
        if target in item.lower() or item.lower() in target:
            player.inventory.remove(item)
            rooms[room_name]['items'][item] = "Something you set down."
            print(f"You set down the {item}.")
            return
    print(f"You're not carrying a '{target}'.")


# ============================================================
# COMBAT ENCOUNTERS
# ============================================================

def _living_room_zombie_encounter(player, rooms):
    """Standard Zombie in the Living Room — triggers once on first entry."""
    if 'living_room_zombie_cleared' in player.story_flags:
        return

    separator()
    slow_print(
        "The figure near the overturned bookcase turns.\n"
        "A zombie — shambling, slow, but it's between you and the room.\n"
        "There's no walking past it."
    )
    time.sleep(0.3)
    slow_print("This is your first real fight.")
    time.sleep(0.2)
    separator()

    enemy  = make_standard_zombie()
    result = combat_loop(player, enemy)

    if result == 'win':
        separator()
        slow_print("The room is clear. Your pulse is hammering.")
        slow_print("That was real. That just happened.")
        player.story_flags['living_room_zombie_cleared'] = True
        player.hidden_stats['Survival Skill'] += 1
        player.add_note('clues',
            "You can fight. Remember that.")
        separator()
    elif result == 'escaped':
        separator()
        slow_print("You back off — the zombie loses interest for a moment.")
        slow_print("The living room is still accessible, but be ready.")
        player.story_flags['living_room_zombie_cleared'] = True
        separator()
    elif result == 'lose':
        separator()
        slow_print("You go down in the living room.")
        slow_print("No one finds you.")
        slow_print("\n— GAME OVER —\n")
        separator()
        sys.exit()


def _bathroom_zombie_encounter(room_name, rooms, player):
    """Patient Zero combat encounter — replaces moral dilemma in v5."""
    separator()
    slow_print(
        "It stirs when you get close. A former patient — hospital gown,\n"
        "IV port still taped to its arm, bare feet on the cold tile.\n"
        "Its eyes find you — clouded. Some small, failing awareness.\n"
        "It used to be a person. Not long ago."
    )
    print()
    time.sleep(0.3)
    slow_print("It's moving toward you now. You don't have a choice.")
    time.sleep(0.2)
    separator()

    enemy  = make_patient_zombie()
    result = combat_loop(player, enemy)

    if result == 'win':
        separator()
        slow_print("It's over. The bathroom is quiet.")
        print()
        slow_print("Your hands won't stop shaking.")
        slow_print("You weren't sure you could do that.")
        slow_print("Now you know.")
        player.story_flags['bathroom_zombie_resolved'] = True
        player.story_flags['bathroom_zombie_mercy']    = True
        player.story_flags['showed_mercy']             = True
        player.hidden_stats['Mental Stability']        = max(0, player.hidden_stats['Mental Stability'] - 2)
        player.hidden_stats['Alpha Awareness']         += 1
        player.hidden_stats['Survival Skill']          += 1
        rooms['Bathroom']['objects'].pop('figure', None)
        player.add_note('clues',
            "Patient Zero — bathroom. You ended its suffering. Something in you responded that you didn't expect.")
        separator()

    elif result == 'escaped':
        separator()
        slow_print("You back out of the bathroom, pulse slamming.")
        slow_print("It watches you leave. Something in those clouded eyes tracks you\nall the way to the door.")
        player.story_flags['bathroom_zombie_resolved'] = True
        player.story_flags['bathroom_zombie_left']     = True
        player.hidden_stats['Mental Stability']        = max(0, player.hidden_stats['Mental Stability'] - 1)
        separator()

    elif result == 'lose':
        separator()
        slow_print("The infection spreads faster than expected.")
        slow_print("The ceiling is the last thing you see.")
        slow_print("\n— GAME OVER —\n")
        separator()
        sys.exit()


# ============================================================
# V6: NEW ZOMBIE ENCOUNTERS
# ============================================================

def _entrance_hall_zombie_encounter(player, rooms):
    """Unavoidable first combat encounter — teaches the system."""
    if 'entrance_hall_zombie_cleared' in player.story_flags:
        return
    separator()
    slow_print(
        "A zombie — dead-eyed, slow — is blocking the hallway.\n"
        "It turns toward you as you step off the stairs."
    )
    time.sleep(0.3)
    slow_print("This is your first fight. You don't have a choice.")
    time.sleep(0.2)
    separator()
    enemy  = make_entrance_zombie()
    result = combat_loop(player, enemy)
    if result == 'win':
        separator()
        slow_print("The hallway is clear.")
        slow_print("Your hands are shaking. Your pulse is loud in your ears.")
        slow_print("But you're still standing.")
        player.story_flags['entrance_hall_zombie_cleared'] = True
        player.hidden_stats['Survival Skill'] += 1
        player.add_note('clues', "You can fight. You should expect more.")
        separator()
    elif result == 'escaped':
        separator()
        slow_print("You back down the stairs — it loses interest.")
        player.story_flags['entrance_hall_zombie_cleared'] = True
        separator()
    elif result == 'lose':
        separator()
        slow_print("You go down in the entrance hall before you even started.")
        slow_print("\n— GAME OVER —\n")
        separator()
        sys.exit()


def _kitchen_zombie_encounter(player, rooms):
    """Scavenger zombie in the Kitchen — first entry."""
    if 'kitchen_zombie_cleared' in player.story_flags:
        return
    separator()
    slow_print(
        "Something is moving near the stripped cabinets.\n"
        "A zombie in torn clothes — scavenging through the empty shelves.\n"
        "It hasn't heard you yet. But it will."
    )
    time.sleep(0.2)
    separator()
    enemy  = make_kitchen_zombie()
    result = combat_loop(player, enemy)
    if result in ('win', 'escaped'):
        slow_print("The kitchen is clear." if result == 'win' else "You slip out — it loses interest in you.")
        player.story_flags['kitchen_zombie_cleared'] = True
        if result == 'win':
            player.hidden_stats['Survival Skill'] += 1
        separator()
    elif result == 'lose':
        separator()
        slow_print("The kitchen floor is the last thing you see.")
        slow_print("\n— GAME OVER —\n")
        separator()
        sys.exit()


def _study_zombie_encounter(player, rooms):
    """Zombie hunched over the research desk — first entry."""
    if 'study_zombie_cleared' in player.story_flags:
        return
    separator()
    slow_print(
        "There's a zombie at the research desk.\n"
        "It's hunched over the notes — almost like it's reading them.\n"
        "It turns toward you as you enter."
    )
    time.sleep(0.2)
    separator()
    enemy  = make_study_zombie()
    result = combat_loop(player, enemy)
    if result in ('win', 'escaped'):
        slow_print("The study is yours." if result == 'win' else "You back out — it doesn't follow.")
        player.story_flags['study_zombie_cleared'] = True
        if result == 'win':
            player.hidden_stats['Survival Skill'] += 1
        separator()
    elif result == 'lose':
        separator()
        slow_print("The study floor is cold.")
        slow_print("\n— GAME OVER —\n")
        separator()
        sys.exit()


def _closet_zombie_encounter(player, rooms):
    """Burst zombie in Master Bedroom closet — triggered by EXAMINE CLOSET."""
    separator()
    slow_print("You reach for the closet door—")
    time.sleep(0.4)
    slow_print("It explodes open.")
    time.sleep(0.2)
    slow_print("Something lurches out directly at you.")
    time.sleep(0.1)
    separator()
    enemy  = make_closet_zombie()
    result = combat_loop(player, enemy)
    if result == 'win':
        separator()
        slow_print("It goes down. Your heart is hammering.")
        slow_print("The closet is clear now.")
        player.story_flags['closet_zombie_resolved'] = True
        player.hidden_stats['Survival Skill'] += 1
        separator()
    elif result == 'escaped':
        separator()
        slow_print("You scramble back — it doesn't follow far.")
        player.story_flags['closet_zombie_resolved'] = True
        separator()
    elif result == 'lose':
        separator()
        slow_print("You never even had time to react properly.")
        slow_print("\n— GAME OVER —\n")
        separator()
        sys.exit()


def _lab_zombie_encounter(player, rooms):
    """Lab technician zombie in the Lab Wing — first entry."""
    if 'lab_zombie_cleared' in player.story_flags:
        return
    separator()
    slow_print(
        "A figure in tattered scrubs — a lab technician.\n"
        "The scrubs still have a name tag, but it's too bloodstained to read.\n"
        "One hand still holds a broken syringe.\n"
        "It turns toward you."
    )
    time.sleep(0.3)
    separator()
    enemy  = make_lab_tech_zombie()
    result = combat_loop(player, enemy)
    if result in ('win', 'escaped'):
        slow_print("The lab is clear." if result == 'win' else "You retreat — it stays in the lab.")
        player.story_flags['lab_zombie_cleared'] = True
        if result == 'win':
            player.hidden_stats['Survival Skill'] += 1
            player.hidden_stats['Alpha Awareness'] += 1
            slow_print("Facing something that was nearly a doctor — something about that hits differently.")
        separator()
    elif result == 'lose':
        separator()
        slow_print("The lab floor is the last thing you see.")
        slow_print("\n— GAME OVER —\n")
        separator()
        sys.exit()


# ============================================================
# FINAL ENCOUNTER — BARBADOS (V6)
# ============================================================

def encounter_barbados(player, rooms):
    separator()
    slow_print("Barbados moves.")
    time.sleep(0.5)
    slow_print("Not fast — but with terrible purpose.")
    time.sleep(0.3)
    slow_print("His eyes find you in the dark. Pale. Luminous. Knowing.")
    print()
    time.sleep(0.5)
    slow_print("He knows what you are.")
    slow_print("He made you.")
    time.sleep(0.4)
    separator()
    slow_print("This is what you came here for.")
    time.sleep(0.3)
    separator()

    enemy  = make_barbados()
    result = combat_loop(player, enemy)

    if result == 'lose':
        separator()
        slow_print("He crosses the room faster than something dead should move.")
        slow_print("The last thing you see is his eyes — pale, aware, almost sad.")
        slow_print("Almost human.")
        print()
        slow_print("— GAME OVER —\n")
        separator()
        sys.exit()

    # ── Player won — determine ending ──
    separator()
    slow_print("Barbados falls.")
    time.sleep(0.4)
    slow_print("For a moment — just a moment — the pale light leaves his eyes.")
    slow_print("Something human flickers there. Confusion. Recognition.")
    slow_print("Then it's gone.")
    print()
    time.sleep(0.7)

    knows_full    = 'knows_full_truth'                  in player.story_flags
    has_camp      = 'knows_camp_location'               in player.story_flags
    read_warning  = 'found_kristys_warning'             in player.story_flags
    knows_truth   = 'knows_barbados_self_injected'      in player.story_flags
    knows_comp    = 'knows_protagonist_is_subject_01'   in player.story_flags
    showed_mercy  = 'showed_mercy'                      in player.story_flags
    told_unknown  = 'told_maya_unknown'                 in player.story_flags
    told_clean    = 'told_maya_clean'                   in player.story_flags

    # ── BEST ENDING: full truth + knows the way out ──
    if knows_full and has_camp:
        slow_print("You read everything they left behind.")
        slow_print("You know who he was. What he did. What he made you.")
        print()
        if showed_mercy:
            slow_print("You showed mercy in that bathroom. You didn't have to.")
            slow_print("You understood the difference between ending suffering\n"
                       "and causing it. That matters.")
            print()
        if told_unknown:
            slow_print("You told Maya you didn't know if you were infected.\n"
                       "She knew what that meant. She was ready for it.\n"
                       "She's been looking for someone like you.")
        elif told_clean:
            slow_print("You told Maya you were clean. Maybe you believe that.\n"
                       "Maybe it's even true — in the way that matters.")
        print()
        slow_print("You move northwest. Four kilometres.")
        slow_print("Maya's voice comes through the walkie-talkie as you reach\n"
                   "the community centre gate: 'I see you. Come in.'")
        print()
        slow_print("There are things that need answers.")
        slow_print("You carry the only ones that matter.")
        print()
        _ending_title("THE TRUTH — YOU CARRY IT NOW")

    # ── GOOD ENDING: knows the core story ──
    elif read_warning and knows_truth and knows_comp:
        slow_print("You understand what happened here.")
        slow_print("What was done to these people. What was done to you.")
        print()
        if showed_mercy:
            slow_print("You showed mercy where you could.")
            slow_print("That cost you something. But you didn't lose yourself.")
            print()
        slow_print("You walk out as the grey sky begins to lighten.")
        slow_print("The world is broken.")
        slow_print("You carry a secret that could change what comes next.")
        print()
        _ending_title("ESCAPED — WITH THE TRUTH")

    # ── SURVIVAL ENDING: got out, missed the full picture ──
    else:
        slow_print("You don't fully understand what just happened.")
        slow_print("You don't know exactly what you are.")
        print()
        if showed_mercy:
            slow_print("You made a choice in that bathroom.\n"
                       "You're still not sure what it says about you.")
            print()
        slow_print("But you're still standing.")
        slow_print("Whatever Barbados made you — it's enough.")
        print()
        slow_print("You walk out into the grey morning and don't look back.")
        print()
        _ending_title("ESCAPED — FOR NOW")


def _ending_title(title):
    separator()
    pad = (55 - len(title)) // 2
    slow_print(" " * pad + title)
    separator()
    sys.exit()


# ============================================================
# RADIO
# ============================================================

def action_radio(player):
    if not player.has_item('walkie-talkie'):
        print("You're not carrying anything to broadcast on.")
        return

    if ('heard_first_signal' not in player.story_flags and
            'heard_maya_broadcast' not in player.story_flags):
        print("Only static. You haven't picked up a signal yet.")
        return

    if player.turns - player.last_radio_turn < 5:
        print("Static. No response yet.")
        return

    separator()
    player.last_radio_turn = player.turns

    if 'maya_responded' not in player.story_flags:
        slow_print("You key the transmit button. Your voice sounds strange to your ears.")
        slow_print(
            "  'Hello — is anyone out there? I just woke up in some kind\n"
            "  of lab. I don't know where I am. I don't know how long\n"
            "  I've been out.'"
        )
        time.sleep(0.8)
        print()
        slow_print("Static. Then:")
        time.sleep(0.6)
        slow_print(
            "  [MAYA]: 'Copy that. We've been tracking an anomalous signal\n"
            "   from a research compound on the east side of the city.\n"
            "   That's where you are — an old private facility.\n\n"
            "   My name's Maya. We have a camp about four kilometres\n"
            "   northwest. Old community centre.\n\n"
            "   Listen: whatever is in that building with you — it knows\n"
            "   you're there. It's been in there a long time. It's been\n"
            "   waiting.\n\n"
            "   If you can get out — just run. Come to us.\n"
            "   Frequency 7.4. We'll be on it.'"
        )
        print()
        slow_print("A pause. Then:")
        slow_print("  [MAYA]: '...Are you infected?'")
        time.sleep(0.5)
        print()

        while True:
            resp = input(
                "  [1] 'No. I'm clean.'\n"
                "  [2] 'I don't know. I genuinely don't know.'\n"
                "  > "
            ).strip()
            if resp in ('1', '2'):
                break
            print("Choose 1 or 2.")

        print()
        if resp == '1':
            slow_print(
                "  [MAYA]: 'Good. Then get out of there.\n"
                "   We'll have a team ready when you arrive.'"
            )
            player.story_flags['told_maya_clean'] = True
        else:
            slow_print(
                "  [MAYA]: '...\n"
                "   Then you might be exactly who we've been looking for.\n"
                "   Get out of there. Come to us. There are things you need to know.'"
            )
            player.story_flags['told_maya_unknown'] = True
            player.hidden_stats['Alpha Awareness']  += 1

        player.story_flags['maya_responded']      = True
        player.story_flags['knows_camp_location']  = True
        player.add_note('people',
            "Maya — survivor. Running a camp ~4km northwest. Frequency 7.4. She told you where you are.")
        player.add_note('clues',
            "Maya's camp: old community centre, northwest. She's waiting. Don't come infected.")

    else:
        slow_print("You key the button.")
        time.sleep(0.5)
        slow_print(
            "  [MAYA]: 'Still receiving you. Get out of that building.\n"
            "   We're on 7.4. Don't take longer than you have to.'"
        )

    separator()


# ============================================================
# NOTES, MAP, HINT
# ============================================================

def show_notes(player):
    separator()
    print("YOUR NOTES")
    print()

    if not player.notes['people'] and not player.notes['clues']:
        print("  Nothing recorded yet. Read documents and examine the environment.")
        separator()
        return

    if player.notes['people']:
        print("PEOPLE")
        for entry in player.notes['people']:
            print(f"  · {entry}")
        print()

    if player.notes['clues']:
        print("KEY CLUES")
        for entry in player.notes['clues']:
            print(f"  · {entry}")

    separator()


def show_map(current_room, visited_rooms):
    def mark(room):
        if room == current_room: return "★"
        if room in visited_rooms: return "■"
        return "·"

    r = {name: mark(name) for name in [
        "Bathroom", "Master Bedroom", "Quarantine Room", "Living Room",
        "Kitchen", "Study", "Parlor", "Entrance Hall", "Cloakroom",
        "Basement", "Lab Wing"
    ]}

    separator()
    print("MANSION MAP")
    print("  ★ you are here    ■ visited    · unknown\n")
    print(f"                     {r['Bathroom']} Bathroom")
    print(f"                          |")
    print(f"                     {r['Master Bedroom']} Master Bedroom")
    print(f"                          |")
    print(f"  {r['Quarantine Room']} Quarantine Room ──── {r['Living Room']} Living Room")
    print(f"                          |")
    print(f"                     {r['Kitchen']} Kitchen ──── {r['Study']} Study")
    print(f"                          |")
    print(f"  {r['Parlor']} Parlor ──── {r['Entrance Hall']} Entrance Hall ──── {r['Cloakroom']} Cloakroom")
    print(f"                          |")
    print(f"                     {r['Basement']} Basement ──── {r['Lab Wing']} Lab Wing")
    separator()


def action_hint(room_name, player):
    separator()
    print("HINT")
    print()
    flags = player.story_flags

    hints = []

    if not player.has_item('flashlight') and room_name == 'Basement':
        hints.append("There are items in this room — try GET to pick them up.")
    if player.has_item('quarantine key') and 'quarantine_opened' not in flags:
        hints.append("You have the quarantine key. The quarantine room is west of the living room.")
    if 'knows_key_in_study' in flags and not player.has_item('quarantine key'):
        hints.append("Kristy's letter said the quarantine key is in the study. The study is east of the kitchen.")
    if 'generator_started' not in flags and room_name == 'Basement':
        hints.append("The generator is in this room. EXAMINE it, then USE FLASHLIGHT ON GENERATOR to start it.")
    if player.has_item('walkie-talkie') and 'maya_responded' not in flags and 'heard_first_signal' in flags:
        hints.append("You picked up a signal on the walkie-talkie. Try RADIO to respond.")
    if not player.notes['people']:
        hints.append("Try READING the documents you find. They'll fill in your NOTES automatically.")
    if len(player.visited_rooms) < 4:
        hints.append("Use PEEK [direction] to preview a room before entering it.")
    if 'bathroom_zombie_resolved' not in flags and room_name == 'Bathroom':
        hints.append("EXAMINE the figure — it's a combat encounter, not just atmosphere.")
    if room_name == 'Study' and not player.has_item('quarantine key'):
        hints.append("There's a quarantine key in this room. GET it.")
    if room_name == 'Living Room' and 'found_kristys_warning' not in flags:
        hints.append("There's a letter on the floor. You can READ it here — no need to pick it up first.")
    if player.hp < player.max_hp // 2:
        hints.append("Your HP is low. Use a first aid kit or food to recover before the next fight.")

    if hints:
        for h in hints[:3]:
            print(f"  → {h}")
    else:
        print("  You're doing fine. Keep exploring and reading what you find.")

    separator()


# ============================================================
# SURVIVAL SYSTEM
# ============================================================

def update_survival(player):
    player.turns += 1

    if player.turns % 12 == 0:
        player.survival['hunger'] -= 3
    if player.turns % 10 == 0:
        player.survival['thirst'] -= 5
    if player.turns % 15 == 0:
        player.survival['stress'] = min(100, player.survival['stress'] + 1)

    if player.survival['hunger'] <= 20:
        slow_print("Your stomach cramps. You need to eat.")
    if player.survival['thirst'] <= 20:
        slow_print("Your throat is raw. You need water.")
    if player.survival['stress'] >= 70:
        slow_print("Your hands won't stop shaking. Keep it together.")

    if player.survival['stress'] >= 80:
        player.hidden_stats['Mental Stability'] = max(0,
            player.hidden_stats['Mental Stability'] - 1)

    if player.survival['hunger'] <= 0:
        separator()
        slow_print("Your body gives out. It's quiet at least.")
        slow_print("You never find out what was waiting in the quarantine room.")
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

    check_timed_events(player)


# ============================================================
# OPENING + HELP
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
        "Fluorescent lights flicker above. Cracks in the ceiling.",
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
    print("(Type HELP anytime. Type NOTES to track what you've learned. Type MAP to see where you've been.)")
    print()
    input("(Press Enter to begin...)\n")


def show_help():
    separator()
    print("HOW TO PLAY\n")
    print("  MOVEMENT")
    print("  north / south / east / west   move in a direction  (n/s/e/w also work)")
    print("  peek [direction]               preview a room before entering")
    print()
    print("  EXPLORATION")
    print("  look                           full room description")
    print("  examine [object]               examine something closely")
    print("  read [item]                    read a document — works without picking it up")
    print("  get [item]                     pick up an item")
    print("  drop [item]                    drop an item")
    print()
    print("  ITEMS")
    print("  use [item]                     use an item")
    print("  use [item] on [target]         use an item on something specific")
    print("  eat [food]                     eat food")
    print("  drink [water]                  drink water")
    print("  start [generator]              start a machine")
    print("  radio                          use the walkie-talkie")
    print()
    print("  COMBAT  (turn-based — Pokémon-style)")
    print("  Choose a numbered move each turn. Type counts matter — some moves")
    print("  are super effective (2×) or not very effective (0.5×) vs certain enemy types.")
    print("  Guard reduces the next hit by 40%. Use Item heals mid-fight.")
    print("  Unlock stronger moves as your Alpha Awareness stat grows.")
    print()
    print("  INFO")
    print("  inventory  (or i)              what you're carrying")
    print("  stats                          your stats and HP")
    print("  notes                          your lore codex — fills in as you discover things")
    print("  map                            ASCII map of rooms you've visited")
    print("  hint                           contextual nudge if you're stuck")
    print("  help                           this screen")
    print("  quit                           exit")
    separator()


# ============================================================
# MAIN LOOP
# ============================================================

def main():
    opening_scene()

    player  = Player()
    rooms   = build_rooms()
    current = 'Basement'

    player.visited_rooms.add(current)
    action_enter_room(current, rooms, player)

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
                print("Read what?")

        elif verb == 'get':
            if target:
                action_get(target, current, rooms, player)
            else:
                print("Get what?")

        elif verb == 'drop':
            if target:
                action_drop(target, current, rooms, player)
            else:
                print("Drop what?")

        elif verb == 'inventory':
            player.show_inventory()

        elif verb == 'stats':
            player.show_stats()

        elif verb == 'help':
            show_help()

        elif verb == 'notes':
            show_notes(player)

        elif verb == 'map':
            show_map(current, player.visited_rooms)

        elif verb == 'hint':
            action_hint(current, player)

        elif verb == 'peek':
            if target:
                action_peek(target, current, rooms, player)
            else:
                print("Peek which direction? (north, south, east, west)")

        elif verb == 'go':
            new_room = action_go(target, current, rooms, player)
            if new_room != current:
                current = new_room
                player.visited_rooms.add(current)
                action_enter_room(current, rooms, player)
                # V6: 8 combat encounters across the mansion
                if current == 'Entrance Hall':
                    _entrance_hall_zombie_encounter(player, rooms)
                if current == 'Living Room':
                    _living_room_zombie_encounter(player, rooms)
                if current == 'Kitchen':
                    _kitchen_zombie_encounter(player, rooms)
                if current == 'Study':
                    _study_zombie_encounter(player, rooms)
                if current == 'Lab Wing':
                    _lab_zombie_encounter(player, rooms)
                if current == 'Quarantine Room':
                    encounter_barbados(player, rooms)

        elif verb == 'use':
            if isinstance(target, tuple):
                action_use(target[0], target[1], current, rooms, player)
            elif target:
                action_use(target, None, current, rooms, player)
            else:
                print("Use what?")

        elif verb == 'eat':
            if target:
                action_eat(target, rooms, current, player)
            else:
                print("Eat what?")

        elif verb == 'drink':
            if target:
                action_drink(target, rooms, current, player)
            else:
                print("Drink what?")

        elif verb == 'open':
            tgt = (target or '').lower()
            if current == 'Entrance Hall' and any(w in tgt for w in ('door', 'front', 'plank', 'barricade')):
                separator()
                print("The front door is barricaded from this side — heavy planks, nailed hard.\n"
                      "There's no opening it by hand.\n"
                      "Even if you pried it open, out there is worse than in here. For now.")
                separator()
            else:
                print("Try: USE [key] ON [door], or just GO in a direction.")

        elif verb == 'start':
            action_start(target or 'generator', current, rooms, player)

        elif verb == 'radio':
            action_radio(player)

        elif verb == 'unknown':
            print(f"Not sure what '{target}' means. Type HELP for commands, HINT if you're stuck.")

        else:
            print("The mansion waits. What do you do?")

        update_survival(player)


if __name__ == "__main__":
    main()
