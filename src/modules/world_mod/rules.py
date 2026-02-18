from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from src.utils.logger import logger


@dataclass
class Rule:
    """Represents a rule that can be applied to the world state."""
    name: str
    description: str
    priority: int = 0
    enabled: bool = True
    condition: Optional[Callable[[Any], bool]] = None
    action: Optional[Callable[[Any], None]] = None

    def check(self, world_state: Any) -> bool:
        """Check if the rule condition is met."""
        if not self.enabled:
            return False
        if self.condition is None:
            return True
        return self.condition(world_state)

    def apply(self, world_state: Any):
        """Apply the rule action."""
        if self.action and self.check(world_state):
            self.action(world_state)
            logger.debug(f"Rule '{self.name}' applied")


class RulesEngine:
    """
    Rules engine for managing and applying world rules.
    Implements "Code as Law" - rules define how the world behaves.
    """

    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._rule_order: List[str] = []

    def register_rule(self, rule: Rule):
        """
        Register a rule with the engine.

        Args:
            rule: The rule to register
        """
        self._rules[rule.name] = rule
        self._rule_order.append(rule.name)
        self._rule_order.sort(key=lambda n: self._rules[n].priority, reverse=True)
        logger.info(f"Rule registered: {rule.name}")

    def unregister_rule(self, rule_name: str):
        """
        Unregister a rule.

        Args:
            rule_name: Name of the rule to remove
        """
        if rule_name in self._rules:
            del self._rules[rule_name]
            self._rule_order.remove(rule_name)
            logger.info(f"Rule unregistered: {rule_name}")

    def enable_rule(self, rule_name: str):
        """Enable a rule."""
        if rule_name in self._rules:
            self._rules[rule_name].enabled = True
            logger.info(f"Rule enabled: {rule_name}")

    def disable_rule(self, rule_name: str):
        """Disable a rule."""
        if rule_name in self._rules:
            self._rules[rule_name].enabled = False
            logger.info(f"Rule disabled: {rule_name}")

    def apply_rules(self, world_state: Any) -> List[str]:
        """
        Apply all enabled rules in priority order.

        Args:
            world_state: The current world state

        Returns:
            List of rule names that were applied
        """
        applied = []
        for rule_name in self._rule_order:
            rule = self._rules[rule_name]
            if rule.check(world_state):
                rule.apply(world_state)
                applied.append(rule_name)

        if applied:
            logger.debug(f"Applied rules: {applied}")

        return applied

    def get_rules(self, enabled_only: bool = False) -> List[Rule]:
        """
        Get all registered rules.

        Args:
            enabled_only: If True, only return enabled rules

        Returns:
            List of rules
        """
        if enabled_only:
            return [r for r in self._rules.values() if r.enabled]
        return list(self._rules.values())

    def clear_rules(self):
        """Clear all registered rules."""
        self._rules.clear()
        self._rule_order.clear()
        logger.info("All rules cleared")


# Common rule templates
class RuleTemplates:
    """Common rule templates for world simulation."""

    @staticmethod
    def create_threshold_rule(
        name: str,
        description: str,
        attribute_path: str,
        threshold: float,
        comparison: str = "gte",
        action: Optional[Callable[[Any], None]] = None
    ) -> Rule:
        """
        Create a rule that triggers when an attribute crosses a threshold.

        Args:
            name: Rule name
            description: Rule description
            attribute_path: Dot-separated path to the attribute (e.g., "character.health")
            threshold: Threshold value
            comparison: Comparison type ('gt', 'gte', 'lt', 'lte', 'eq')
            action: Action to perform when triggered
        """
        def condition(world_state):
            value = RulesEngine._get_attribute(world_state, attribute_path)
            if value is None:
                return False

            ops = {
                'gt': lambda a, b: a > b,
                'gte': lambda a, b: a >= b,
                'lt': lambda a, b: a < b,
                'lte': lambda a, b: a <= b,
                'eq': lambda a, b: a == b
            }
            return ops.get(comparison, lambda a, b: a >= b)(value, threshold)

        return Rule(
            name=name,
            description=description,
            condition=condition,
            action=action
        )

    @staticmethod
    def create_periodic_rule(
        name: str,
        description: str,
        interval: int,
        action: Callable[[Any], None]
    ) -> Rule:
        """
        Create a rule that triggers at regular intervals.

        Args:
            name: Rule name
            description: Rule description
            interval: Number of ticks between triggers
            action: Action to perform
        """
        last_trigger = {'tick': 0}

        def condition(world_state):
            current_tick = getattr(world_state, 'tick_count', 0)
            if current_tick - last_trigger['tick'] >= interval:
                last_trigger['tick'] = current_tick
                return True
            return False

        return Rule(
            name=name,
            description=description,
            condition=condition,
            action=action
        )

    @staticmethod
    def create_event_rule(
        name: str,
        description: str,
        event_type: str,
        action: Callable[[Any], None]
    ) -> Rule:
        """
        Create a rule that triggers on a specific event.

        Args:
            name: Rule name
            description: Rule description
            event_type: Type of event to listen for
            action: Action to perform
        """
        def condition(world_state):
            pending_events = getattr(world_state, 'pending_events', [])
            return any(e.get('type') == event_type for e in pending_events)

        return Rule(
            name=name,
            description=description,
            condition=condition,
            action=action
        )
