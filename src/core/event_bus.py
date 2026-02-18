from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from src.utils.logger import logger


@dataclass
class Event:
    """Represents an event in the simulation."""
    event_type: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "system"

    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            'event_type': self.event_type,
            'data': self.data,
            'timestamp': self.timestamp,
            'source': self.source
        }


class EventBus:
    """
    Central event bus for handling injections, interactions, and internal events.
    Implements a publish-subscribe pattern for decoupled communication.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._event_history: List[Event] = []
        self._max_history: int = 1000

    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        """
        Subscribe to a specific event type.

        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is published
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event type: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]):
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            callback: The callback to remove
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
            logger.debug(f"Unsubscribed from event type: {event_type}")

    def publish(self, event: Event):
        """
        Publish an event to all subscribers.

        Args:
            event: The event to publish
        """
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        # Notify subscribers
        subscribers = self._subscribers.get(event.event_type, [])
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback for {event.event_type}: {e}")

        # Also notify wildcard subscribers
        wildcard_subscribers = self._subscribers.get('*', [])
        for callback in wildcard_subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in wildcard event callback: {e}")

        logger.debug(f"Event published: {event.event_type}")

    def emit(self, event_type: str, data: Dict[str, Any], source: str = "system"):
        """
        Convenience method to create and publish an event.

        Args:
            event_type: Type of event
            data: Event data payload
            source: Event source identifier
        """
        event = Event(event_type=event_type, data=data, source=source)
        self.publish(event)

    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """
        Retrieve event history.

        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return

        Returns:
            List of events matching the criteria
        """
        if event_type:
            events = [e for e in self._event_history if e.event_type == event_type]
        else:
            events = self._event_history.copy()

        return events[-limit:]

    def clear_history(self):
        """Clear the event history."""
        self._event_history.clear()
        logger.info("Event history cleared")


# Common event types
class EventTypes:
    """Standard event types used across the simulation."""

    # Injection events
    CHARACTER_ADDED = "character_added"
    CHARACTER_REMOVED = "character_removed"
    CHARACTER_MODIFIED = "character_modified"

    # Item events
    ITEM_CREATED = "item_created"
    ITEM_DESTROYED = "item_destroyed"
    ITEM_TRANSFERRED = "item_transferred"

    # World events
    WORLD_STATE_CHANGED = "world_state_changed"
    TICK_COMPLETED = "tick_completed"

    # Story events
    STORY_GENERATED = "story_generated"
    SCENE_CHANGED = "scene_changed"

    # Game events
    PLAYER_ACTION = "player_action"
    GAME_STATE_CHANGED = "game_state_changed"

    # Custom injection events
    CUSTOM_INJECTION = "custom_injection"
