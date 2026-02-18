"""
Cyberpunk City World Module

A cyberpunk-themed world implementation for RIW2.
Features corporate intrigue, netrunning, and street-level survival.
"""

from typing import Dict, Any, Optional
import os
from src.core.entities import Character, Item
from src.modules.world_mod.rules import Rule, RuleTemplates
from universe.base_world import BaseWorld, WorldConfig
from src.utils.logger import logger


class CyberpunkCityWorld(BaseWorld):
    """
    Cyberpunk city world implementation.

    Features:
    - Corporate surveillance system
    - Netrunning mechanics
    - Faction reputation
    - Black market economy
    """

    def __init__(self, world_id: str = "cyberpunk_city"):
        # Load config from file
        config_path = os.path.join(
            os.path.dirname(__file__),
            "config.yaml"
        )

        if os.path.exists(config_path):
            config = WorldConfig.from_yaml(config_path)
        else:
            config = WorldConfig(
                name="Neo Tokyo 2087",
                theme="cyberpunk",
                description="A cyberpunk metropolis"
            )

        super().__init__(world_id, config)

        # Faction reputation tracking
        self.faction_reputation: Dict[str, int] = {
            "arasaka": 0,
            "militech": 0,
            "netrunners": 0
        }

        # Surveillance level (0-5)
        self.surveillance_level = 0

    def _register_custom_rules(self):
        """Register cyberpunk-specific rules."""

        # Rule: Corporate surveillance increases when in corporate zones
        def check_surveillance(world):
            # Find player character (or any character in corporate zone)
            for char in world.characters.values():
                if char.location == "corporate_tower":
                    return True
            return False

        def apply_surveillance(world):
            self.surveillance_level = min(5, self.surveillance_level + 1)
            logger.info(f"Corporate surveillance level increased to {self.surveillance_level}")

        surveillance_rule = Rule(
            name="corporate_surveillance",
            description="Surveillance increases when in corporate zones",
            priority=5,
            condition=check_surveillance,
            action=apply_surveillance
        )
        self.rules_engine.register_rule(surveillance_rule)

        # Rule: Passive surveillance decay
        def decay_surveillance(world):
            if self.surveillance_level > 0:
                self.surveillance_level = max(0, self.surveillance_level - 1)

        decay_rule = RuleTemplates.create_periodic_rule(
            name="surveillance_decay",
            description="Surveillance slowly decreases over time",
            interval=10,
            action=decay_surveillance
        )
        self.rules_engine.register_rule(decay_rule)

        # Rule: Netrunner hideout reduces surveillance
        def check_hideout(world):
            for char in world.characters.values():
                if char.location == "netrunner_hideout":
                    return True
            return False

        def apply_hideout(world):
            self.surveillance_level = max(0, self.surveillance_level - 2)
            logger.info("Surveillance reduced by netrunner countermeasures")

        hideout_rule = Rule(
            name="netrunner_countermeasures",
            description="Netrunner hideout reduces surveillance",
            priority=6,
            condition=check_hideout,
            action=apply_hideout
        )
        self.rules_engine.register_rule(hideout_rule)

    def modify_faction_reputation(self, faction: str, amount: int):
        """
        Modify reputation with a faction.

        Args:
            faction: Faction ID
            amount: Reputation change (-100 to 100)
        """
        if faction in self.faction_reputation:
            current = self.faction_reputation[faction]
            self.faction_reputation[faction] = max(-100, min(100, current + amount))
            logger.info(f"Faction {faction} reputation: {self.faction_reputation[faction]}")

    def get_faction_status(self, faction: str) -> str:
        """Get the relationship status with a faction."""
        rep = self.faction_reputation.get(faction, 0)

        if rep >= 80:
            return "allied"
        elif rep >= 40:
            return "friendly"
        elif rep >= -40:
            return "neutral"
        elif rep >= -80:
            return "hostile"
        else:
            return "enemy"

    def can_access_location(self, character: Character, location_id: str) -> bool:
        """
        Check if a character can access a location.

        Args:
            character: The character trying to access
            location_id: Target location ID

        Returns:
            True if access is allowed
        """
        location = self.locations.get(location_id)
        if not location:
            return False

        # Check restricted locations
        if location.properties.get("restricted", False):
            # Corporate tower requires keycard or high stealth
            if location_id == "corporate_tower":
                has_keycard = any(
                    self.items.get(item_id) and self.items[item_id].name == "Level 5 Keycard"
                    for item_id in character.inventory
                )
                if not has_keycard:
                    stealth = character.attributes.get("stealth", 0)
                    if stealth < 20:
                        logger.info(f"{character.name} denied access to Corporate Tower")
                        return False

        return True

    def tick(self):
        """Override tick to add cyberpunk-specific behavior."""
        super().tick()

        # Random encounters based on location
        self._process_random_encounters()

    def _process_random_encounters(self):
        """Process random encounters based on character locations."""
        # Simple implementation - can be expanded
        for char in self.characters.values():
            if char.location == "slums":
                # Higher chance of encounters in slums
                if self.tick_count % 5 == 0:
                    logger.debug(f"Random encounter check for {char.name} in Slums")


def create_cyberpunk_city() -> CyberpunkCityWorld:
    """Factory function to create a Cyberpunk City world."""
    world = CyberpunkCityWorld()
    world.initialize()
    return world


# Additional helper functions for the cyberpunk world

def create_netrunner_character(name: str, hacking_skill: int = 50) -> Character:
    """Create a netrunner character with appropriate attributes."""
    return Character(
        name=name,
        description=f"A skilled netrunner with {hacking_skill} hacking ability",
        health=60,
        energy=150,
        attributes={
            "hacking": hacking_skill,
            "stealth": 20,
            "max_health": 60,
            "max_energy": 150
        }
    )


def create_corp_soldier_character(name: str, combat_level: int = 5) -> Character:
    """Create a corporate soldier character."""
    return Character(
        name=name,
        description=f"A corporate security operative",
        health=100 + (combat_level * 20),
        energy=100,
        level=combat_level,
        attributes={
            "attack": 15 + (combat_level * 3),
            "defense": 10 + (combat_level * 2),
            "loyalty": 80,
            "max_health": 100 + (combat_level * 20)
        }
    )


def create_cyberware_item(name: str, cyberware_type: str, bonus: int) -> Item:
    """Create a cyberware implant item."""
    return Item(
        name=name,
        item_type="cyberware",
        rarity="rare",
        value=1000 + (bonus * 100),
        attributes={
            "cyberware_type": cyberware_type,
            "bonus": bonus,
            "equipped": False
        }
    )
