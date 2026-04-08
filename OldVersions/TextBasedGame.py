# Davon Gass - Zombie Apocalypse Text Adventure Game

def show_instructions():
    """Print the main menu and the commands."""
    print("\nZombie Apocalypse Text Adventure Game")
    print("Collect all essential items to win the game, or be caught by the Alpha Zombie.")
    print("Move commands: go North, go East, go South, go West")
    print("To pick up an item just type 'get item_name'")
    print("Type 'show instructions' to see this message again.\n")



def move_player(current_room, direction, rooms, inventory):
    """Move the player to a different room if possible, checking for locked doors."""
    next_room = rooms[current_room].get(direction)
    if next_room:
        if current_room == 'Living Room' and direction == 'West' and 'Key' not in inventory:
            print("\nThe door to the Attic is locked. You need a key to enter.\n")
            return current_room
        return next_room
    else:
        print("\nYou can't go that way.\n")
        return current_room


def encounter_alpha(current_room, rooms, inventory):
    if current_room == 'Attic':
        missing_items = [item for item in required_items if item not in inventory]
        if not missing_items:  # If no items are missing
            print("\nWith all items in hand, you confront the Alpha Zombie...")
            print("After a fierce battle, you defeat the zombie and escape the house! YOU WIN!")
            return "won"
        else:
            print("\nAs you enter the Attic unprepared, facing the Alpha Zombie...")
            print(f"You were missing {', '.join(missing_items)} and were overpowered... GAME OVER!")
            return "lost"
    return None  # Continue the game if not in the Attic





def get_item(item, current_room, rooms, inventory):
    """Get an item from the room if available, in a case-insensitive manner."""
    item = ' '.join(item).lower()  # Convert the entire item name to lowercase for comparison
    if 'item' in rooms[current_room] and rooms[current_room]['item'].lower() == item:
        inventory.append(rooms[current_room]['item'])  # Add the original item name to the inventory
        print(f"\n{rooms[current_room]['item']} added to your inventory.\n")
        rooms[current_room]['item'] = None
    else:
        print(f"\n{item} is not in this room.\n")



def check_win_condition(inventory, rooms, current_room):
    """Check if the player has met the win condition."""
    if 'Alpha Zombie' in rooms[current_room] and set(required_items).issubset(set(inventory)):
        return "won"
    elif 'Alpha Zombie' in rooms[current_room]:
        return "lost"
    return "continue"


# Required items to win the game
required_items = ['Key', 'First Aid Kit', 'Food Supplies', 'Flashlight', 'Walkie-Talkie']


def main():
    rooms = {
        'Entrance Hall': {'South': 'Basement', 'item': None},
        'Basement': {'North': 'Entrance Hall', 'West': 'Living Room', 'item': 'Flashlight'},
        'Living Room': {'East': 'Basement', 'South': 'Kitchen', 'North': 'Master Bedroom', 'West': 'Attic', 'item': 'Key'},
        'Kitchen': {'North': 'Living Room', 'East': 'Study', 'item': 'Food Supplies'},
        'Study': {'West': 'Kitchen', 'item': 'Walkie-Talkie'},
        'Master Bedroom': {'South': 'Living Room', 'East': 'Bathroom', 'item': None},
        'Bathroom': {'West': 'Master Bedroom', 'item': 'First Aid Kit'},
        'Attic': {'West': 'Living Room', 'item': 'Alpha Zombie'}
    }

    inventory = []
    current_room = 'Entrance Hall'
    show_instructions()

    while True:
        print(f"\nYou are in the {current_room}.\n")
        if 'item' in rooms[current_room] and rooms[current_room]['item']:
            print(f"You see a {rooms[current_room]['item']}\n")
        command = input("Enter your move: ").lower().split()

        # Handle input
        if command[0] == 'go' and len(command) > 1:
            new_room = move_player(current_room, command[1].capitalize(), rooms, inventory)
            if new_room != current_room:
                current_room = new_room
                encounter_result = encounter_alpha(current_room, rooms, inventory)
                if encounter_result == "won":
                    break  # Player won the game
                elif encounter_result == "lost":
                    break  # Player lost the game




        elif command[0] == 'get' and len(command) > 1:
            get_item(command[1:], current_room, rooms, inventory)
        elif ' '.join(command) == 'show instructions':
            show_instructions()
        else:
            print("\nInvalid command.\n")


if __name__ == "__main__":
    main()
