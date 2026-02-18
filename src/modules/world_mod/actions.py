from typing import Dict, List, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from src.utils.logger import logger

if TYPE_CHECKING:
    from src.core.entities import Character, Item, Location


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    side_effects: List[str] = field(default_factory=list)


class Action:
    """Base class for all actions in the simulation."""

    name: str = "base_action"
    description: str = "Base action"

    def __init__(self, actor: 'Character', target: Optional[Any] = None):
        self.actor = actor
        self.target = target

    def check_requirements(self) -> bool:
        """Check if action requirements are met."""
        return True

    def execute(self, world_state: Any) -> ActionResult:
        """Execute the action."""
        raise NotImplementedError

    def get_cost(self) -> Dict[str, int]:
        """Get the cost of performing this action."""
        return {}


class MoveAction(Action):
    """Action to move a character to a different location."""

    name = "move"
    description = "Move to a different location"

    def __init__(self, actor: 'Character', destination: str):
        super().__init__(actor)
        self.destination = destination

    def check_requirements(self) -> bool:
        if self.actor.energy < 5:
            return False
        return True

    def execute(self, world_state: Any) -> ActionResult:
        if not self.check_requirements():
            return ActionResult(
                success=False,
                message="Not enough energy to move"
            )

        # Find location
        locations = getattr(world_state, 'locations', {})
        if self.destination not in locations:
            return ActionResult(
                success=False,
                message=f"Location '{self.destination}' not found"
            )

        # Update character location
        old_location = self.actor.location
        self.actor.location = self.destination

        # Update location entities
        if old_location and old_location in locations:
            locations[old_location].remove_character(self.actor.id)

        locations[self.destination].add_character(self.actor.id)
        self.actor.energy -= 5

        return ActionResult(
            success=True,
            message=f"{self.actor.name} moved to {self.destination}",
            data={'from': old_location, 'to': self.destination}
        )


class InteractAction(Action):
    """Action to interact with another character."""

    name = "interact"
    description = "Interact with another character"

    def __init__(self, actor: 'Character', target: 'Character', interaction_type: str = "talk"):
        super().__init__(actor, target)
        self.interaction_type = interaction_type

    def check_requirements(self) -> bool:
        if self.actor.energy < 10:
            return False
        if self.actor.location != self.target.location:
            return False
        return True

    def execute(self, world_state: Any) -> ActionResult:
        if not self.check_requirements():
            return ActionResult(
                success=False,
                message="Cannot interact: requirements not met"
            )

        # Update relationship based on interaction
        affinity_change = {
            "talk": 5,
            "trade": 10,
            "help": 15,
            "attack": -20,
            "ignore": -5
        }.get(self.interaction_type, 0)

        current_rel = self.actor.get_relationship(self.target.id)
        self.actor.set_relationship(self.target.id, current_rel + affinity_change)

        self.actor.energy -= 10

        return ActionResult(
            success=True,
            message=f"{self.actor.name} {self.interaction_type}s with {self.target.name}",
            data={
                'interaction': self.interaction_type,
                'affinity_change': affinity_change
            }
        )


class UseItemAction(Action):
    """Action to use an item."""

    name = "use_item"
    description = "Use an item from inventory"

    def __init__(self, actor: 'Character', item: 'Item', target: Optional[Any] = None):
        super().__init__(actor, target)
        self.item = item

    def check_requirements(self) -> bool:
        if self.item.id not in self.actor.inventory:
            return False
        if self.actor.energy < self.item.attributes.get('energy_cost', 0):
            return False
        return True

    def execute(self, world_state: Any) -> ActionResult:
        if not self.check_requirements():
            return ActionResult(
                success=False,
                message="Cannot use item: requirements not met"
            )

        energy_cost = self.item.attributes.get('energy_cost', 0)
        self.actor.energy -= energy_cost

        # Apply item effects
        effects = self.item.attributes.get('effects', {})
        for effect, value in effects.items():
            if effect == 'heal':
                self.actor.heal(value)
            elif effect == 'damage':
                self.actor.take_damage(value)
            elif effect == 'energy':
                self.actor.energy = min(100, self.actor.energy + value)

        # Handle consumable
        if self.item.item_type == "consumable":
            self.actor.remove_item(self.item.id)

        return ActionResult(
            success=True,
            message=f"{self.actor.name} used {self.item.name}",
            data={'item': self.item.name, 'effects': list(effects.keys())}
        )


class AttackAction(Action):
    """Action to attack another character."""

    name = "attack"
    description = "Attack another character"

    def __init__(self, actor: 'Character', target: 'Character'):
        super().__init__(actor, target)

    def check_requirements(self) -> bool:
        if self.actor.energy < 20:
            return False
        if self.actor.location != self.target.location:
            return False
        return True

    def execute(self, world_state: Any) -> ActionResult:
        if not self.check_requirements():
            return ActionResult(
                success=False,
                message="Cannot attack: requirements not met"
            )

        # Calculate damage
        base_damage = self.actor.attributes.get('attack', 10)
        weapon_bonus = 0

        # Check for equipped weapon
        for item_id in self.actor.inventory:
            items = getattr(world_state, 'items', {})
            if item_id in items:
                item = items[item_id]
                if item.attributes.get('equipped', False) and item.item_type == "weapon":
                    weapon_bonus = item.attributes.get('damage', 0)

        total_damage = base_damage + weapon_bonus
        actual_damage = self.target.take_damage(total_damage)
        self.actor.energy -= 20

        # Gain experience for dealing damage
        self.actor.gain_experience(actual_damage)

        # Update relationship
        current_rel = self.actor.get_relationship(self.target.id)
        self.actor.set_relationship(self.target.id, current_rel - 20)

        return ActionResult(
            success=True,
            message=f"{self.actor.name} attacks {self.target.name} for {actual_damage} damage",
            data={
                'damage': actual_damage,
                'target_health': self.target.health
            },
            side_effects=['combat_log_entry']
        )


class RestAction(Action):
    """Action to rest and recover."""

    name = "rest"
    description = "Rest to recover health and energy"

    def check_requirements(self) -> bool:
        return True

    def execute(self, world_state: Any) -> ActionResult:
        # Recover health and energy
        health_recover = self.actor.attributes.get('health_regen', 5)
        energy_recover = self.actor.attributes.get('energy_regen', 10)

        actual_heal = self.actor.heal(health_recover)
        self.actor.energy = min(100, self.actor.energy + energy_recover)

        return ActionResult(
            success=True,
            message=f"{self.actor.name} rests and recovers",
            data={
                'health_recovered': actual_heal,
                'energy_recovered': energy_recover
            }
        )


class ActionRegistry:
    """Registry for all available actions."""

    _actions: Dict[str, type] = {}

    @classmethod
    def register(cls, action_class: type):
        """Register an action class."""
        cls._actions[action_class.name] = action_class
        logger.info(f"Action registered: {action_class.name}")

    @classmethod
    def get(cls, action_name: str) -> Optional[type]:
        """Get an action class by name."""
        return cls._actions.get(action_name)

    @classmethod
    def create(cls, action_name: str, *args, **kwargs) -> Optional[Action]:
        """Create an action instance."""
        action_class = cls.get(action_name)
        if action_class:
            return action_class(*args, **kwargs)
        return None

    @classmethod
    def list_actions(cls) -> List[str]:
        """List all registered actions."""
        return list(cls._actions.keys())


# Register default actions
ActionRegistry.register(MoveAction)
ActionRegistry.register(InteractAction)
ActionRegistry.register(UseItemAction)
ActionRegistry.register(AttackAction)
ActionRegistry.register(RestAction)
