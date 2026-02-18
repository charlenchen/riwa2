from typing import Dict, List, Any, Optional
import sys
from src.core.entities import Character, Item, Location
from src.modules.world_mod.actions import ActionRegistry, ActionResult
from src.utils.logger import logger


class TextRPG:
    """
    Console-based text RPG interface for testing and playing the simulation.
    Provides an interactive command-line game experience.
    """

    def __init__(self, world_state: Any):
        self.world_state = world_state
        self.player: Optional[Character] = None
        self._running = False
        self._command_history: List[str] = []

    def start(self, player_character: Optional[Character] = None):
        """Start the text RPG."""
        self._running = True

        if player_character:
            self.player = player_character
        else:
            self.player = self._create_character()

        self._print_welcome()
        self._game_loop()

    def stop(self):
        """Stop the text RPG."""
        self._running = False
        logger.info("Text RPG stopped")

    def _print_welcome(self):
        """Print welcome message."""
        print("\n" + "=" * 50)
        print("       RIW2 - Text RPG Interface")
        print("=" * 50)
        print(f"Welcome, {self.player.name}!")
        print("Type 'help' for available commands.\n")
        self._print_status()

    def _game_loop(self):
        """Main game loop."""
        while self._running:
            try:
                command = input("> ").strip()
                if command:
                    self._command_history.append(command)
                    self._process_command(command)
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit.")
            except EOFError:
                self.stop()
                break

    def _process_command(self, command: str):
        """Process a player command."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        commands = {
            'help': self._cmd_help,
            'status': self._cmd_status,
            'look': self._cmd_look,
            'go': self._cmd_go,
            'move': self._cmd_go,
            'inventory': self._cmd_inventory,
            'inv': self._cmd_inventory,
            'use': self._cmd_use,
            'talk': self._cmd_talk,
            'attack': self._cmd_attack,
            'rest': self._cmd_rest,
            'save': self._cmd_save,
            'load': self._cmd_load,
            'quit': self._cmd_quit,
            'exit': self._cmd_quit
        }

        handler = commands.get(cmd)
        if handler:
            handler(args)
        else:
            print(f"Unknown command: {cmd}. Type 'help' for commands.")

    def _cmd_help(self, args: str):
        """Show help information."""
        print("""
Available Commands:
  status          - Show character status
  look            - Examine current location
  go <location>   - Move to a location
  inventory       - Show your inventory
  use <item>      - Use an item
  talk <character>- Talk to a character
  attack <target> - Attack a target
  rest            - Rest to recover
  save            - Save game state
  load            - Load saved game
  quit            - Exit the game
""")

    def _cmd_status(self, args: str):
        """Show character status."""
        self._print_status()

    def _print_status(self):
        """Print character status."""
        if not self.player:
            return

        print(f"\n--- {self.player.name} ---")
        print(f"Health: {self.player.health}/100")
        print(f"Energy: {self.player.energy}/100")
        print(f"Level: {self.player.level} (EXP: {self.player.experience})")
        print(f"Location: {self.player.location or 'Unknown'}")
        print(f"Status: {self.player.status}")
        print()

    def _cmd_look(self, args: str):
        """Examine current location."""
        if not self.player or not self.player.location:
            print("You are nowhere. Everything is dark.")
            return

        locations = getattr(self.world_state, 'locations', {})
        location = locations.get(self.player.location)

        if not location:
            print(f"You are at {self.player.location}, but details are unclear.")
            return

        print(f"\n=== {location.name} ===")
        print(location.description)

        # Show characters here
        if location.characters:
            print("\nCharacters present:")
            characters = getattr(self.world_state, 'characters', {})
            for char_id in location.characters:
                char = characters.get(char_id)
                if char and char.id != self.player.id:
                    rel = self.player.get_relationship(char.id)
                    rel_str = f"(Relationship: {rel})" if rel != 0 else ""
                    print(f"  - {char.name} {rel_str}")

        # Show items here
        if location.items:
            print("\nItems on the ground:")
            items = getattr(self.world_state, 'items', {})
            for item_id in location.items:
                item = items.get(item_id)
                if item:
                    print(f"  - {item.name}")

        # Show exits
        if location.connected_locations:
            print("\nExits:")
            for loc_id in location.connected_locations:
                loc = locations.get(loc_id)
                if loc:
                    print(f"  - {loc.name}")
        print()

    def _cmd_go(self, args: str):
        """Move to a location."""
        if not args:
            print("Go where? Specify a location name.")
            return

        if not self.player:
            return

        # Find location by name or ID
        locations = getattr(self.world_state, 'locations', {})
        target = None
        for loc_id, loc in locations.items():
            if loc_id.lower() == args.lower() or loc.name.lower() == args.lower():
                target = loc_id
                break

        if not target:
            print(f"Cannot find '{args}'.")
            return

        # Execute move action
        action = ActionRegistry.create('move', self.player, target)
        if action:
            result = action.execute(self.world_state)
            self._print_action_result(result)
        else:
            print("Cannot perform that action.")

    def _cmd_inventory(self, args: str):
        """Show inventory."""
        if not self.player:
            return

        print("\n--- Inventory ---")
        if not self.player.inventory:
            print("Your inventory is empty.")
        else:
            items = getattr(self.world_state, 'items', {})
            for item_id in self.player.inventory:
                item = items.get(item_id)
                if item:
                    equipped = " (equipped)" if item.attributes.get('equipped') else ""
                    print(f"  - {item.name}{equipped}")
        print()

    def _cmd_use(self, args: str):
        """Use an item."""
        if not args:
            print("Use what? Specify an item name.")
            return

        if not self.player:
            return

        # Find item in inventory
        items = getattr(self.world_state, 'items', {})
        target_item = None
        for item_id in self.player.inventory:
            item = items.get(item_id)
            if item and item.name.lower() == args.lower():
                target_item = item
                break

        if not target_item:
            print(f"You don't have '{args}'.")
            return

        action = ActionRegistry.create('use_item', self.player, target_item)
        if action:
            result = action.execute(self.world_state)
            self._print_action_result(result)
        else:
            print("Cannot use that item.")

    def _cmd_talk(self, args: str):
        """Talk to a character."""
        if not args:
            print("Talk to whom? Specify a character name.")
            return

        self._interact_with_character(args, 'talk')

    def _cmd_attack(self, args: str):
        """Attack a character."""
        if not args:
            print("Attack whom? Specify a target name.")
            return

        self._interact_with_character(args, 'attack')

    def _interact_with_character(self, name: str, interaction_type: str):
        """Helper to interact with a character."""
        if not self.player or not self.player.location:
            return

        # Find character in current location
        locations = getattr(self.world_state, 'locations', {})
        location = locations.get(self.player.location)

        if not location:
            return

        characters = getattr(self.world_state, 'characters', {})
        target = None
        for char_id in location.characters:
            char = characters.get(char_id)
            if char and char.name.lower() == name.lower() and char.id != self.player.id:
                target = char
                break

        if not target:
            print(f"Cannot find '{name}' here.")
            return

        action = ActionRegistry.create(interaction_type, self.player, target)
        if action:
            result = action.execute(self.world_state)
            self._print_action_result(result)
        else:
            print(f"Cannot {interaction_type} with {name}.")

    def _cmd_rest(self, args: str):
        """Rest to recover."""
        if not self.player:
            return

        action = ActionRegistry.create('rest', self.player)
        if action:
            result = action.execute(self.world_state)
            self._print_action_result(result)
        else:
            print("Cannot rest here.")

    def _cmd_save(self, args: str):
        """Save game state."""
        print("Game save functionality - to be implemented with StateManager")
        # TODO: Integrate with StateManager

    def _cmd_load(self, args: str):
        """Load saved game."""
        print("Game load functionality - to be implemented with StateManager")
        # TODO: Integrate with StateManager

    def _cmd_quit(self, args: str):
        """Quit the game."""
        print("Thanks for playing!")
        self.stop()

    def _print_action_result(self, result: ActionResult):
        """Print the result of an action."""
        if result.success:
            print(f"✓ {result.message}")
        else:
            print(f"✗ {result.message}")

    def _create_character(self) -> Character:
        """Create a new character through prompts."""
        print("\n--- Character Creation ---")
        name = input("Enter your character's name: ").strip() or "Hero"

        print("\nChoose your class:")
        print("1. Warrior (High health, high attack)")
        print("2. Mage (High energy, magic abilities)")
        print("3. Rogue (Balanced, high speed)")

        choice = input("Choice (1-3): ").strip()

        attributes = {}
        if choice == '1':
            attributes = {'max_health': 150, 'attack': 15, 'defense': 10}
        elif choice == '2':
            attributes = {'max_health': 80, 'energy': 150, 'magic': 20}
        else:
            attributes = {'max_health': 100, 'speed': 15, 'crit_chance': 0.2}

        character = Character(
            name=name,
            description=f"A brave adventurer in the world of RIW2",
            attributes=attributes
        )

        # Add starting items
        starter_items = self._get_starter_items(choice)
        for item in starter_items:
            character.add_item(item.id)
            # Add items to world state
            items = getattr(self.world_state, 'items', {})
            items[item.id] = item

        print(f"\nWelcome, {name}! Your adventure begins...")
        return character

    def _get_starter_items(self, class_choice: str) -> List[Item]:
        """Get starter items based on class choice."""
        items = []

        if class_choice == '1':  # Warrior
            items.append(Item(
                name="Iron Sword",
                item_type="weapon",
                attributes={'damage': 10, 'equipped': True}
            ))
            items.append(Item(
                name="Health Potion",
                item_type="consumable",
                attributes={'effects': {'heal': 50}}
            ))
        elif class_choice == '2':  # Mage
            items.append(Item(
                name="Wooden Staff",
                item_type="weapon",
                attributes={'damage': 5, 'equipped': True}
            ))
            items.append(Item(
                name="Energy Potion",
                item_type="consumable",
                attributes={'effects': {'energy': 50}}
            ))
        else:  # Rogue
            items.append(Item(
                name="Dagger",
                item_type="weapon",
                attributes={'damage': 8, 'equipped': True}
            ))
            items.append(Item(
                name="Bandage",
                item_type="consumable",
                attributes={'effects': {'heal': 30}}
            ))

        # Assign IDs
        for i, item in enumerate(items):
            item.id = f"starter_item_{i}"

        return items


def run_text_rpg(world_state: Any):
    """Convenience function to run the text RPG."""
    game = TextRPG(world_state)
    try:
        game.start()
    except KeyboardInterrupt:
        game.stop()
