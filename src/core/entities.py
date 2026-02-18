from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from uuid import uuid4
from datetime import datetime


@dataclass
class Entity:
    """Base class for all entities in the simulation."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert entity to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'attributes': self.attributes,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Entity':
        """Create entity from dictionary."""
        return cls(
            id=data.get('id', str(uuid4())),
            name=data.get('name', ''),
            description=data.get('description', ''),
            created_at=data.get('created_at', datetime.now().isoformat()),
            attributes=data.get('attributes', {}),
            metadata=data.get('metadata', {})
        )

    def update_attribute(self, key: str, value: Any):
        """Update a single attribute."""
        self.attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get an attribute value."""
        return self.attributes.get(key, default)


@dataclass
class Character(Entity):
    """Represents a character in the simulation."""
    health: int = 100
    energy: int = 100
    level: int = 1
    experience: int = 0
    inventory: List[str] = field(default_factory=list)
    location: Optional[str] = None
    status: str = "active"  # active, inactive, removed
    relationships: Dict[str, int] = field(default_factory=dict)  # character_id -> affinity

    def to_dict(self) -> dict:
        """Convert character to dictionary."""
        data = super().to_dict()
        data.update({
            'health': self.health,
            'energy': self.energy,
            'level': self.level,
            'experience': self.experience,
            'inventory': self.inventory,
            'location': self.location,
            'status': self.status,
            'relationships': self.relationships
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        """Create character from dictionary."""
        char = super().from_dict(data)
        char.health = data.get('health', 100)
        char.energy = data.get('energy', 100)
        char.level = data.get('level', 1)
        char.experience = data.get('experience', 0)
        char.inventory = data.get('inventory', [])
        char.location = data.get('location')
        char.status = data.get('status', 'active')
        char.relationships = data.get('relationships', {})
        return char

    def take_damage(self, amount: int) -> int:
        """
        Apply damage to the character.
        Returns actual damage taken.
        """
        actual_damage = max(0, min(amount, self.health))
        self.health -= actual_damage
        if self.health <= 0:
            self.status = "inactive"
        return actual_damage

    def heal(self, amount: int) -> int:
        """
        Heal the character.
        Returns actual amount healed.
        """
        max_health = self.get_attribute('max_health', 100)
        actual_heal = min(amount, max_health - self.health)
        self.health += actual_heal
        return actual_heal

    def gain_experience(self, amount: int) -> bool:
        """
        Add experience and potentially level up.
        Returns True if leveled up.
        """
        self.experience += amount
        exp_needed = self.level * 100

        if self.experience >= exp_needed:
            self.experience -= exp_needed
            self.level += 1
            self.health = self.get_attribute('max_health', 100)  # Full heal on level up
            return True
        return False

    def add_item(self, item_id: str):
        """Add an item to inventory."""
        self.inventory.append(item_id)

    def remove_item(self, item_id: str) -> bool:
        """Remove an item from inventory."""
        if item_id in self.inventory:
            self.inventory.remove(item_id)
            return True
        return False

    def set_relationship(self, character_id: str, affinity: int):
        """Set relationship affinity with another character (-100 to 100)."""
        self.relationships[character_id] = max(-100, min(100, affinity))

    def get_relationship(self, character_id: str) -> int:
        """Get relationship affinity with another character."""
        return self.relationships.get(character_id, 0)


@dataclass
class Item(Entity):
    """Represents an item in the simulation."""
    item_type: str = "generic"  # weapon, armor, consumable, key, etc.
    rarity: str = "common"  # common, uncommon, rare, epic, legendary
    value: int = 0
    stackable: bool = False
    stack_size: int = 1
    max_stack: int = 99
    owner_id: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert item to dictionary."""
        data = super().to_dict()
        data.update({
            'item_type': self.item_type,
            'rarity': self.rarity,
            'value': self.value,
            'stackable': self.stackable,
            'stack_size': self.stack_size,
            'max_stack': self.max_stack,
            'owner_id': self.owner_id,
            'location': self.location
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Item':
        """Create item from dictionary."""
        item = super().from_dict(data)
        item.item_type = data.get('item_type', 'generic')
        item.rarity = data.get('rarity', 'common')
        item.value = data.get('value', 0)
        item.stackable = data.get('stackable', False)
        item.stack_size = data.get('stack_size', 1)
        item.max_stack = data.get('max_stack', 99)
        item.owner_id = data.get('owner_id')
        item.location = data.get('location')
        return item

    def use(self, target: Optional[Entity] = None) -> bool:
        """
        Use the item. Override in subclasses for specific behavior.
        Returns True if use was successful.
        """
        if self.item_type == "consumable":
            self.stack_size -= 1
            return True
        return False


@dataclass
class Location(Entity):
    """Represents a location in the world."""
    location_type: str = "generic"
    parent_location: Optional[str] = None
    connected_locations: List[str] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert location to dictionary."""
        data = super().to_dict()
        data.update({
            'location_type': self.location_type,
            'parent_location': self.parent_location,
            'connected_locations': self.connected_locations,
            'characters': self.characters,
            'items': self.items,
            'properties': self.properties
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Location':
        """Create location from dictionary."""
        loc = super().from_dict(data)
        loc.location_type = data.get('location_type', 'generic')
        loc.parent_location = data.get('parent_location')
        loc.connected_locations = data.get('connected_locations', [])
        loc.characters = data.get('characters', [])
        loc.items = data.get('items', [])
        loc.properties = data.get('properties', {})
        return loc

    def add_character(self, character_id: str):
        """Add a character to this location."""
        if character_id not in self.characters:
            self.characters.append(character_id)

    def remove_character(self, character_id: str):
        """Remove a character from this location."""
        if character_id in self.characters:
            self.characters.remove(character_id)

    def add_item(self, item_id: str):
        """Add an item to this location."""
        if item_id not in self.items:
            self.items.append(item_id)

    def remove_item(self, item_id: str):
        """Remove an item from this location."""
        if item_id in self.items:
            self.items.remove(item_id)
