from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader, BaseLoader
from src.utils.logger import logger


@dataclass
class StorySegment:
    """Represents a segment of generated story."""
    tick_start: int
    tick_end: int
    content: str
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            'tick_start': self.tick_start,
            'tick_end': self.tick_end,
            'content': self.content,
            'summary': self.summary,
            'metadata': self.metadata,
            'created_at': self.created_at
        }


class Narrator:
    """
    LLM-driven narrator that converts simulation logs into narrative content.
    Implements "Log to Story" functionality.
    """

    def __init__(
        self,
        template_dir: str = "src/modules/story_mod/prompt_templates",
        llm_client: Optional[Any] = None,
        style: str = "default"
    ):
        self.template_dir = template_dir
        self.llm_client = llm_client
        self.style = style
        self._story_segments: List[StorySegment] = []
        self._pending_logs: List[Dict[str, Any]] = []

        # Setup Jinja2 environment
        if os.path.exists(template_dir):
            self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        else:
            self.jinja_env = Environment(loader=BaseLoader())
            logger.warning(f"Template directory not found: {template_dir}")

        # Load default templates if they exist
        self._load_templates()

    def _load_templates(self):
        """Load prompt templates."""
        self.templates = {}

        template_names = [
            'default_story',
            'battle_scene',
            'character_introduction',
            'world_description',
            'dialogue_scene'
        ]

        for name in template_names:
            try:
                self.templates[name] = self.jinja_env.get_template(f"{name}.jinja2")
            except Exception:
                # Use default template if specific one not found
                pass

    def add_log(self, log_entry: Dict[str, Any]):
        """
        Add a log entry to the pending logs.

        Args:
            log_entry: Dictionary containing log data
        """
        self._pending_logs.append(log_entry)

    def add_logs(self, log_entries: List[Dict[str, Any]]):
        """Add multiple log entries."""
        self._pending_logs.extend(log_entries)

    def generate_story(
        self,
        world_state: Any,
        tick_start: int,
        tick_end: int,
        style: Optional[str] = None
    ) -> StorySegment:
        """
        Generate a story segment from simulation logs.

        Args:
            world_state: Current world state
            tick_start: Starting tick number
            tick_end: Ending tick number
            style: Optional writing style override

        Returns:
            Generated story segment
        """
        style = style or self.style

        # Filter logs for the specified tick range
        relevant_logs = [
            log for log in self._pending_logs
            if tick_start <= log.get('tick', 0) <= tick_end
        ]

        if not relevant_logs:
            return StorySegment(
                tick_start=tick_start,
                tick_end=tick_end,
                content="",
                summary="No events occurred."
            )

        # Build context for LLM
        context = self._build_context(world_state, relevant_logs)

        # Generate story using LLM or template
        if self.llm_client:
            content = self._generate_with_llm(context, style)
        else:
            content = self._generate_with_template(context, style)

        # Create summary
        summary = self._generate_summary(relevant_logs)

        segment = StorySegment(
            tick_start=tick_start,
            tick_end=tick_end,
            content=content,
            summary=summary,
            metadata={
                'log_count': len(relevant_logs),
                'style': style,
                'events': [log.get('event_type') for log in relevant_logs]
            }
        )

        self._story_segments.append(segment)
        self._pending_logs = [
            log for log in self._pending_logs
            if log.get('tick', 0) > tick_end
        ]

        logger.info(f"Generated story segment for ticks {tick_start}-{tick_end}")
        return segment

    def _build_context(self, world_state: Any, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build context dictionary for story generation."""
        context = {
            'logs': logs,
            'world_state': self._serialize_world_state(world_state),
            'style': self.style
        }

        # Extract characters involved
        characters = set()
        for log in logs:
            data = log.get('data', {})
            if 'character' in data:
                characters.add(data['character'])
            if 'actor' in data:
                characters.add(data['actor'])
            if 'target' in data:
                characters.add(data['target'])

        context['characters'] = list(characters)

        return context

    def _serialize_world_state(self, world_state: Any) -> Dict[str, Any]:
        """Serialize world state for LLM context."""
        if hasattr(world_state, 'to_dict'):
            return world_state.to_dict()

        # Basic serialization
        result = {}
        for attr in ['tick_count', 'locations', 'characters', 'items']:
            if hasattr(world_state, attr):
                value = getattr(world_state, attr)
                if isinstance(value, dict):
                    result[attr] = {k: v.to_dict() if hasattr(v, 'to_dict') else v
                                   for k, v in value.items()}
                elif isinstance(value, list):
                    result[attr] = [v.to_dict() if hasattr(v, 'to_dict') else v
                                   for v in value]
                else:
                    result[attr] = value

        return result

    def _generate_with_llm(self, context: Dict[str, Any], style: str) -> str:
        """Generate story using LLM."""
        # Get appropriate template
        template = self.templates.get('default_story')

        if template:
            prompt = template.render(**context)
        else:
            prompt = self._build_default_prompt(context)

        # Call LLM
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                style=style
            )
            return response
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_with_template(context, style)

    def _generate_with_template(self, context: Dict[str, Any], style: str) -> str:
        """Generate story using template-based approach."""
        events = context.get('logs', [])

        paragraphs = []
        for event in events:
            event_type = event.get('event_type', 'unknown')
            data = event.get('data', {})

            paragraph = self._format_event(event_type, data, style)
            if paragraph:
                paragraphs.append(paragraph)

        return "\n\n".join(paragraphs) if paragraphs else "Nothing notable happened."

    def _format_event(self, event_type: str, data: Dict[str, Any], style: str) -> str:
        """Format a single event into narrative text."""
        formatters = {
            'character_added': lambda d: f"A new figure emerged: {d.get('name', 'Unknown')}.",
            'character_removed': lambda d: f"{d.get('name', 'Someone')} departed from the world.",
            'move': lambda d: f"{d.get('actor', 'Someone')} moved to {d.get('to', 'somewhere')}.",
            'attack': lambda d: f"{d.get('actor', 'Someone')} attacked {d.get('target', 'another')} for {d.get('damage', 0)} damage!",
            'interact': lambda d: f"{d.get('actor', 'Someone')} {d.get('interaction', 'interacted')} with {d.get('target', 'another')}.",
            'rest': lambda d: f"{d.get('actor', 'Someone')} took a moment to rest and recover.",
            'custom_injection': lambda d: f"Reality shifted as something new was injected into the world."
        }

        formatter = formatters.get(event_type, lambda d: f"Something happened: {d}")
        return formatter(data)

    def _generate_summary(self, logs: List[Dict[str, Any]]) -> str:
        """Generate a brief summary of events."""
        if not logs:
            return "No events."

        event_counts = {}
        for log in logs:
            event_type = log.get('event_type', 'unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        parts = [f"{count}x {event_type}" for event_type, count in event_counts.items()]
        return ", ".join(parts)

    def _build_default_prompt(self, context: Dict[str, Any]) -> str:
        """Build a default prompt for LLM."""
        logs_text = "\n".join([
            f"- [{log.get('tick', '?')}] {log.get('event_type')}: {log.get('data', {})}"
            for log in context.get('logs', [])
        ])

        return f"""Based on the following simulation events, write an engaging narrative:

{logs_text}

World State:
{context.get('world_state', {})}

Write in the {context.get('style', 'default')} style. Make it vivid and engaging."""

    def get_story_segments(
        self,
        tick_start: Optional[int] = None,
        tick_end: Optional[int] = None
    ) -> List[StorySegment]:
        """
        Get stored story segments.

        Args:
            tick_start: Optional filter by start tick
            tick_end: Optional filter by end tick

        Returns:
            List of story segments
        """
        segments = self._story_segments.copy()

        if tick_start is not None:
            segments = [s for s in segments if s.tick_end >= tick_start]
        if tick_end is not None:
            segments = [s for s in segments if s.tick_start <= tick_end]

        return segments

    def get_full_story(self) -> str:
        """Get the complete story as a single string."""
        segments = sorted(self._story_segments, key=lambda s: s.tick_start)
        return "\n\n---\n\n".join(s.content for s in segments)

    def export_story(self, filepath: str, format: str = "text") -> bool:
        """
        Export the story to a file.

        Args:
            filepath: Output file path
            format: Export format ('text', 'json')

        Returns:
            True if successful
        """
        try:
            if format == "json":
                import json
                data = [s.to_dict() for s in self._story_segments]
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                with open(filepath, 'w') as f:
                    f.write(self.get_full_story())

            logger.info(f"Story exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export story: {e}")
            return False
