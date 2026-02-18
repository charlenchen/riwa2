from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import os
import yaml
from src.core.entities import Character, Item, Location
from src.core.event_bus import EventBus, Event
from src.modules.world_mod.rules import RulesEngine
from src.utils.logger import logger


@dataclass
class WorldConfig:
    """Configuration for a world instance."""
    name: str = "Unnamed World"
    description: str = ""
    theme: str = "generic"
    tick_rate: float = 1.0
    max_ticks: int = -1  # -1 for unlimited
    initial_characters: List[Dict[str, Any]] = field(default_factory=list)
    initial_items: List[Dict[str, Any]] = field(default_factory=list)
    initial_locations: List[Dict[str, Any]] = field(default_factory=list)
    custom_rules: List[Dict[str, Any]] = field(default_factory=list)
    world_properties: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, filepath: str) -> 'WorldConfig':
        """Load configuration from a YAML file."""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        return cls(
            name=data.get('name', 'Unnamed World'),
            description=data.get('description', ''),
            theme=data.get('theme', 'generic'),
            tick_rate=data.get('tick_rate', 1.0),
            max_ticks=data.get('max_ticks', -1),
            initial_characters=data.get('initial_characters', []),
            initial_items=data.get('initial_items', []),
            initial_locations=data.get('initial_locations', []),
            custom_rules=data.get('custom_rules', []),
            world_properties=data.get('world_properties', {})
        )

    @classmethod
    def from_dict(cls, data: dict) -> 'WorldConfig':
        """Create configuration from a dictionary."""
        return cls(
            name=data.get('name', 'Unnamed World'),
            description=data.get('description', ''),
            theme=data.get('theme', 'generic'),
            tick_rate=data.get('tick_rate', 1.0),
            max_ticks=data.get('max_ticks', -1),
            initial_characters=data.get('initial_characters', []),
            initial_items=data.get('initial_items', []),
            initial_locations=data.get('initial_locations', []),
            custom_rules=data.get('custom_rules', []),
            world_properties=data.get('world_properties', {})
        )


class BaseWorld:
    """
    Base class for all world instances.
    Provides core functionality for world simulation, entity management, and event handling.
    """

    def __init__(
        self,
        world_id: str,
        config: Optional[WorldConfig] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.world_id = world_id
        self.config = config or WorldConfig()
        self.event_bus = event_bus or EventBus()

        # Simulation state
        self.tick_count = 0
        self.is_running = False

        # Entity storage
        self.characters: Dict[str, Character] = {}
        self.items: Dict[str, Item] = {}
        self.locations: Dict[str, Location] = {}

        # Systems
        self.rules_engine = RulesEngine()

        # Event logs for story generation
        self.event_log: List[Dict[str, Any]] = []

        # Subscribe to events
        self._setup_event_handlers()

        logger.info(f"World initialized: {self.world_id}")

    def _setup_event_handlers(self):
        """Setup event handlers for the world."""
        self.event_bus.subscribe('*', self._on_any_event)

    def _on_any_event(self, event: Event):
        """Handle any event for logging."""
        self.event_log.append({
            'tick': self.tick_count,
            'event_type': event.event_type,
            'data': event.data,
            'source': event.source,
            'timestamp': event.timestamp
        })

    def initialize(self):
        """Initialize the world with config data."""
        logger.info(f"Initializing world: {self.config.name}")

        # Create initial locations
        for loc_data in self.config.initial_locations:
            self.create_location(loc_data)

        # Create initial items
        for item_data in self.config.initial_items:
            self.create_item(item_data)

        # Create initial characters
        for char_data in self.config.initial_characters:
            self.create_character(char_data)

        # Register custom rules
        self._register_custom_rules()

        logger.info(f"World initialized with {len(self.locations)} locations, "
                   f"{len(self.items)} items, {len(self.characters)} characters")

    def _register_custom_rules(self):
        """Register custom rules from config."""
        # Override in subclasses to register world-specific rules
        pass

    def create_character(self, data: Dict[str, Any]) -> Character:
        """Create a character in the world."""
        character = Character.from_dict(data)
        self.characters[character.id] = character

        # Place character in location if specified
        if character.location and character.location in self.locations:
            self.locations[character.location].add_character(character.id)

        self.event_bus.emit(
            'character_added',
            {'character_id': character.id, 'name': character.name},
            source=self.world_id
        )

        logger.info(f"Character created: {character.name} ({character.id})")
        return character

    def create_item(self, data: Dict[str, Any]) -> Item:
        """Create an item in the world."""
        item = Item.from_dict(data)
        self.items[item.id] = item

        # Place item in location if specified
        if item.location and item.location in self.locations:
            self.locations[item.location].add_item(item.id)

        self.event_bus.emit(
            'item_created',
            {'item_id': item.id, 'name': item.name},
            source=self.world_id
        )

        logger.info(f"Item created: {item.name} ({item.id})")
        return item

    def create_location(self, data: Dict[str, Any]) -> Location:
        """Create a location in the world."""
        location = Location.from_dict(data)
        self.locations[location.id] = location

        self.event_bus.emit(
            'location_created',
            {'location_id': location.id, 'name': location.name},
            source=self.world_id
        )

        logger.info(f"Location created: {location.name} ({location.id})")
        return location

    def remove_character(self, character_id: str):
        """Remove a character from the world."""
        if character_id not in self.characters:
            return

        character = self.characters[character_id]

        # Remove from location
        if character.location and character.location in self.locations:
            self.locations[character.location].remove_character(character_id)

        del self.characters[character_id]

        self.event_bus.emit(
            'character_removed',
            {'character_id': character_id, 'name': character.name},
            source=self.world_id
        )

        logger.info(f"Character removed: {character.name}")

    def tick(self):
        """
        Perform a single simulation tick.
        Override in subclasses for world-specific behavior.
        """
        self.tick_count += 1

        # Apply rules
        self.rules_engine.apply_rules(self)

        # Emit tick event
        self.event_bus.emit(
            'tick_completed',
            {'tick': self.tick_count},
            source=self.world_id
        )

        logger.debug(f"World {self.world_id} tick {self.tick_count} completed")

    def get_state(self) -> Dict[str, Any]:
        """Get the current world state as a dictionary."""
        return {
            'world_id': self.world_id,
            'tick_count': self.tick_count,
            'config': {
                'name': self.config.name,
                'theme': self.config.theme
            },
            'characters': {k: v.to_dict() for k, v in self.characters.items()},
            'items': {k: v.to_dict() for k, v in self.items.items()},
            'locations': {k: v.to_dict() for k, v in self.locations.items()},
            'event_log': self.event_log[-100:]  # Last 100 events
        }

    def to_dict(self) -> Dict[str, Any]:
        """Alias for get_state()."""
        return self.get_state()

    def get_events_since(self, tick: int) -> List[Dict[str, Any]]:
        """Get events that occurred after a specific tick."""
        return [e for e in self.event_log if e['tick'] > tick]

    def get_events_between(self, start_tick: int, end_tick: int) -> List[Dict[str, Any]]:
        """Get events that occurred between two ticks."""
        return [e for e in self.event_log
                if start_tick <= e['tick'] <= end_tick]

    def clear_event_log(self, before_tick: Optional[int] = None):
        """Clear the event log, optionally keeping events after a tick."""
        if before_tick is None:
            self.event_log.clear()
        else:
            self.event_log = [e for e in self.event_log if e['tick'] >= before_tick]

    def find_character_by_name(self, name: str) -> Optional[Character]:
        """Find a character by name (case-insensitive)."""
        name_lower = name.lower()
        for char in self.characters.values():
            if char.name.lower() == name_lower:
                return char
        return None

    def find_location_by_name(self, name: str) -> Optional[Location]:
        """Find a location by name (case-insensitive)."""
        name_lower = name.lower()
        for loc in self.locations.values():
            if loc.name.lower() == name_lower:
                return loc
        return None

    def find_item_by_name(self, name: str) -> Optional[Item]:
        """Find an item by name (case-insensitive)."""
        name_lower = name.lower()
        for item in self.items.values():
            if item.name.lower() == name_lower:
                return item
        return None


# World registry for managing multiple worlds
class WorldRegistry:
    """Registry for managing multiple world instances."""

    _worlds: Dict[str, BaseWorld] = {}

    @classmethod
    def register(cls, world: BaseWorld):
        """Register a world."""
        cls._worlds[world.world_id] = world
        logger.info(f"World registered: {world.world_id}")

    @classmethod
    def get(cls, world_id: str) -> Optional[BaseWorld]:
        """Get a world by ID."""
        return cls._worlds.get(world_id)

    @classmethod
    def list_worlds(cls) -> List[str]:
        """List all registered world IDs."""
        return list(cls._worlds.keys())

    @classmethod
    def remove(cls, world_id: str) -> bool:
        """Remove a world from the registry."""
        if world_id in cls._worlds:
            del cls._worlds[world_id]
            logger.info(f"World removed: {world_id}")
            return True
        return False

    @classmethod
    def clear(cls):
        """Clear all registered worlds."""
        cls._worlds.clear()
        logger.info("World registry cleared")
