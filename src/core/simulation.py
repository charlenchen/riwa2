import time
import os
import json
from typing import Dict, Any, Optional, List
from src.core.state_manager import StateManager
from src.core.event_bus import EventBus, Event, EventTypes
from src.core.entities import Character, Item, Location
from src.modules.story_mod.narrator import Narrator
from src.modules.story_mod.illustrator import Illustrator
from src.utils.llm_client import LLMClient, create_llm_client
from src.utils.logger import logger
from universe.base_world import BaseWorld, WorldConfig, WorldRegistry


class Simulation:
    """
    Main simulation engine for RIW2.
    Integrates World, Story, and Game modules with hot injection and time machine support.
    """

    def __init__(
        self,
        world: Optional[BaseWorld] = None,
        tick_rate: float = 1.0,
        auto_save_interval: int = 10,
        enable_story_generation: bool = True,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize the simulation.

        Args:
            world: World instance to simulate (creates default if None)
            tick_rate: Seconds per tick
            auto_save_interval: Ticks between automatic snapshots
            enable_story_generation: Whether to generate narrative from events
            llm_client: LLM client for story generation (auto-creates if None)
        """
        self.world = world or self._create_default_world()
        self.tick_rate = tick_rate
        self.auto_save_interval = auto_save_interval
        self.enable_story_generation = enable_story_generation

        # Core systems
        self.event_bus = self.world.event_bus
        self.state_manager = StateManager()

        # Story systems
        self.llm_client = llm_client or create_llm_client()
        self.narrator = Narrator(llm_client=self.llm_client) if enable_story_generation else None
        self.illustrator = Illustrator(api_client=self.llm_client) if enable_story_generation else None

        # Simulation state
        self.is_running = False
        self.last_save_tick = 0
        self.story_generation_interval = 10  # Generate story every N ticks

        # Injection handling
        self.inbox_path = "data/inbox"
        self._injection_handlers: Dict[str, callable] = {}
        self._setup_default_injection_handlers()

        # Register world
        WorldRegistry.register(self.world)

        logger.info(f"Simulation initialized with world: {self.world.world_id}")

    def _create_default_world(self) -> BaseWorld:
        """Create a default world instance."""
        config = WorldConfig(
            name="Default World",
            description="A blank world ready for simulation",
            theme="generic"
        )
        world = BaseWorld("default_world", config)
        world.initialize()
        return world

    def _setup_default_injection_handlers(self):
        """Setup default handlers for common injection types."""
        self._injection_handlers = {
            'add_character': self._handle_add_character,
            'remove_character': self._handle_remove_character,
            'add_item': self._handle_add_item,
            'add_location': self._handle_add_location,
            'modify_character': self._handle_modify_character,
            'trigger_event': self._handle_trigger_event,
            'custom': self._handle_custom_injection
        }

    def start(self):
        """Start the simulation engine."""
        logger.info("Starting RIW2 Simulation Engine...")
        self.is_running = True
        self.run_loop()

    def stop(self):
        """Stop the simulation engine."""
        logger.info("Stopping Simulation Engine...")
        self.is_running = False

        # Final save
        self._save_snapshot()

        # Export final story
        if self.narrator:
            self._generate_story_segment()

    def run_loop(self):
        """Main simulation loop."""
        logger.info(f"Simulation running at {self.tick_rate}s per tick")

        while self.is_running:
            start_time = time.time()

            try:
                self.tick()
            except Exception as e:
                logger.error(f"Error in tick: {e}")

            # Maintain tick rate
            elapsed = time.time() - start_time
            sleep_time = max(0, self.tick_rate - elapsed)
            time.sleep(sleep_time)

    def tick(self):
        """Execute a single simulation tick."""
        self.world.tick()

        # Process injections
        self.check_inbox()

        # Generate story periodically
        if self.narrator and self.world.tick_count % self.story_generation_interval == 0:
            self._generate_story_segment()

        # Auto-save
        if self.auto_save_interval > 0:
            if self.world.tick_count - self.last_save_tick >= self.auto_save_interval:
                self._save_snapshot()

        # Log progress
        if self.world.tick_count % 10 == 0:
            logger.info(f"Tick {self.world.tick_count} - Events: {len(self.world.event_log)}")

    def check_inbox(self):
        """Check for and process injection files."""
        if not os.path.exists(self.inbox_path):
            os.makedirs(self.inbox_path, exist_ok=True)
            return

        for filename in os.listdir(self.inbox_path):
            if filename.endswith(".json"):
                file_path = os.path.join(self.inbox_path, filename)
                try:
                    with open(file_path, 'r') as f:
                        injection_data = json.load(f)

                    logger.info(f"Hot Injection Detected: {filename}")
                    self.apply_injection(injection_data)

                    # Archive processed injection
                    self._archive_injection(filename, injection_data)
                    os.remove(file_path)

                except Exception as e:
                    logger.error(f"Error processing injection {filename}: {e}")

    def apply_injection(self, data: Dict[str, Any]):
        """
        Apply an injection to the simulation.

        Args:
            data: Injection data with 'type' field
        """
        injection_type = data.get('type', 'custom')
        handler = self._injection_handlers.get(injection_type)

        if handler:
            handler(data)
        else:
            logger.warning(f"Unknown injection type: {injection_type}")
            self._handle_custom_injection(data)

    def _handle_add_character(self, data: Dict[str, Any]):
        """Handle character addition injection."""
        char_data = {
            'id': data.get('id', f"injected_{data.get('name', 'unknown')}"),
            'name': data.get('name', 'Unknown'),
            'description': data.get('description', 'An injected character'),
            'health': data.get('health', 100),
            'energy': data.get('energy', 100),
            'level': data.get('level', 1),
            'attributes': data.get('attributes', {}),
            'location': data.get('location')
        }
        self.world.create_character(char_data)
        logger.info(f"Character injected: {char_data['name']}")

    def _handle_remove_character(self, data: Dict[str, Any]):
        """Handle character removal injection."""
        char_id = data.get('character_id') or data.get('name')
        if char_id:
            # Try to find by name first
            char = self.world.find_character_by_name(char_id)
            if char:
                self.world.remove_character(char.id)
            else:
                self.world.remove_character(char_id)
            logger.info(f"Character removed: {char_id}")

    def _handle_add_item(self, data: Dict[str, Any]):
        """Handle item addition injection."""
        item_data = {
            'id': data.get('id', f"injected_{data.get('name', 'unknown')}"),
            'name': data.get('name', 'Unknown Item'),
            'description': data.get('description', ''),
            'item_type': data.get('type', 'generic'),
            'rarity': data.get('rarity', 'common'),
            'value': data.get('value', 0),
            'attributes': data.get('attributes', {}),
            'location': data.get('location')
        }
        self.world.create_item(item_data)
        logger.info(f"Item injected: {item_data['name']}")

    def _handle_add_location(self, data: Dict[str, Any]):
        """Handle location addition injection."""
        loc_data = {
            'id': data.get('id', f"injected_{data.get('name', 'unknown')}"),
            'name': data.get('name', 'Unknown Location'),
            'description': data.get('description', ''),
            'location_type': data.get('type', 'generic'),
            'connected_locations': data.get('connections', []),
            'properties': data.get('properties', {})
        }
        self.world.create_location(loc_data)
        logger.info(f"Location injected: {loc_data['name']}")

    def _handle_modify_character(self, data: Dict[str, Any]):
        """Handle character modification injection."""
        char_id = data.get('character_id') or data.get('name')
        if not char_id:
            return

        char = self.world.find_character_by_name(char_id)
        if not char:
            if char_id in self.world.characters:
                char = self.world.characters[char_id]
            else:
                logger.warning(f"Character not found for modification: {char_id}")
                return

        # Apply modifications
        modifications = data.get('modifications', {})
        for key, value in modifications.items():
            if hasattr(char, key):
                setattr(char, key, value)
            elif key in char.attributes:
                char.attributes[key] = value
            else:
                char.attributes[key] = value

        logger.info(f"Character modified: {char.name}")

    def _handle_trigger_event(self, data: Dict[str, Any]):
        """Handle manual event trigger injection."""
        event_type = data.get('event_type', 'custom_injection')
        event_data = data.get('data', {})
        self.event_bus.emit(event_type, event_data, source='injection')
        logger.info(f"Event triggered: {event_type}")

    def _handle_custom_injection(self, data: Dict[str, Any]):
        """Handle custom injection with arbitrary data."""
        logger.info(f"Custom injection: {data}")
        self.event_bus.emit(
            EventTypes.CUSTOM_INJECTION,
            data,
            source='injection'
        )

    def _archive_injection(self, filename: str, data: Dict[str, Any]):
        """Archive processed injection to logs."""
        archive_path = os.path.join("data/logs", "injections.log")
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)

        with open(archive_path, 'a') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {filename}: {json.dumps(data)}\n")

    def _save_snapshot(self):
        """Save a snapshot of the current world state."""
        try:
            self.state_manager.save_snapshot(
                self.world.get_state(),
                self.world.world_id,
                self.world.tick_count
            )
            self.last_save_tick = self.world.tick_count
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")

    def _generate_story_segment(self):
        """Generate a story segment from recent events."""
        if not self.narrator:
            return

        try:
            # Add events to narrator
            events = self.world.get_events_since(
                self.world.tick_count - self.story_generation_interval
            )
            for event in events:
                self.narrator.add_log(event)

            # Generate story
            start_tick = self.world.tick_count - self.story_generation_interval
            segment = self.narrator.generate_story(
                self.world,
                start_tick,
                self.world.tick_count
            )

            if segment.content:
                logger.info(f"Story generated: {segment.summary}")

                # Generate illustration for significant events
                if self.illustrator and 'attack' in segment.metadata.get('events', []):
                    self.illustrator.generate_scene_illustration(segment)

        except Exception as e:
            logger.error(f"Failed to generate story: {e}")

    # Public API for external control

    def save_game(self, name: Optional[str] = None) -> str:
        """
        Manually save the game state.

        Args:
            name: Optional snapshot name

        Returns:
            Path to saved snapshot
        """
        filename = name or f"manual_save_tick_{self.world.tick_count}"
        return self.state_manager.save_snapshot(
            self.world.get_state(),
            self.world.world_id,
            self.world.tick_count
        )

    def load_game(self, snapshot_path: str):
        """
        Load a game state from a snapshot.

        Args:
            snapshot_path: Path to snapshot file
        """
        data = self.state_manager.load_snapshot(snapshot_path)
        self._restore_world_state(data['world_state'])
        logger.info(f"Game loaded from {snapshot_path}")

    def _restore_world_state(self, state: Dict[str, Any]):
        """Restore world state from saved data."""
        # Clear current state
        self.world.characters.clear()
        self.world.items.clear()
        self.world.locations.clear()
        self.world.event_log.clear()

        # Restore tick count
        self.world.tick_count = state.get('tick_count', 0)

        # Restore entities
        for char_id, char_data in state.get('characters', {}).items():
            self.world.characters[char_id] = Character.from_dict(char_data)

        for item_id, item_data in state.get('items', {}).items():
            self.world.items[item_id] = Item.from_dict(item_data)

        for loc_id, loc_data in state.get('locations', {}).items():
            self.world.locations[loc_id] = Location.from_dict(loc_data)

    def list_snapshots(self) -> List[str]:
        """List available snapshots."""
        return self.state_manager.list_snapshots(self.world.world_id)

    def get_world_state(self) -> Dict[str, Any]:
        """Get current world state."""
        return self.world.get_state()

    def get_story(self) -> str:
        """Get the generated story so far."""
        if self.narrator:
            return self.narrator.get_full_story()
        return ""

    def export_story(self, filepath: str):
        """Export the story to a file."""
        if self.narrator:
            self.narrator.export_story(filepath)


if __name__ == "__main__":
    sim = Simulation(tick_rate=1.0, auto_save_interval=30)
    try:
        sim.start()
    except KeyboardInterrupt:
        sim.stop()
        print("\nSimulation terminated.")
