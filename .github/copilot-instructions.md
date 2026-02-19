# RIW2 AI Agent Instructions

## Project Overview

RIW2 is an AI-driven metaverse engine integrating three core systems:
- **World Module**: Logic engine and simulation (physics, rules, actions)
- **Story Module**: LLM-driven narrative generation from simulation logs
- **Game Module**: Interactive procedural game generation and UI bridges

The architecture enforces **engine/content separation**: `src/core/` provides reusable simulation primitives while `universe/` contains world-specific implementations.

## Code Style

**Language**: Python 3.8+  
**Type Hints**: Required for all functions and class methods  
**Dataclasses**: Use `@dataclass` from `dataclasses` for entity definitions (see [src/core/entities.py](src/core/entities.py))  
**Documentation**: Include docstrings for classes and public methods using Google-style format  
**Imports**: Organize as `stdlib → third-party → src modules` with absolute imports from workspace root

Example patterns:
- Entities use `@dataclass` with `field(default_factory=...)` for mutable defaults
- All entities inherit from or follow the `Entity` base class pattern (uuid, name, attributes, metadata)
- JSON serialization via `.to_dict()` / `.from_dict()` class methods

## Architecture

### Core Layers

| Layer | Path | Responsibility |
|-------|------|-----------------|
| **Engine** | `src/core/` | Simulation loop, state management, event bus, entity types, escape protocol, universe state |
| **Modules** | `src/modules/` | World rules, Story generation, Game data export |
| **Utils** | `src/utils/` | LLM client, logging, shared helpers |
| **Content** | `universe/` | World-specific configs, characters, rules (inherit from `BaseWorld`), universal config |
| **Runtime Data** | `data/` | Snapshots, logs, inbox (for hot injection) |

### Key Subsystems

**Simulation Loop** ([src/core/simulation.py](src/core/simulation.py)):
- Tick-based execution with configurable tick_rate (float seconds)
- Auto-save snapshots every N ticks
- Event system integration for hot injection
- State serialization/rollback support

**Universe State** ([src/core/universe_state.py](src/core/universe_state.py)):
- Tracks Celestial Core stellar parameters and migration schedule
- Manages source energy allocation and consumption across worlds
- Records coordinate key fragments and escape gateway locations
- Maintains log of escaped entities

**Escape Protocol** ([src/core/escape_protocol.py](src/core/escape_protocol.py)):
- The termina gateway system for dimensional transcendence
- Fragment collection, coordinate key decryption, printing to real universe
- Supports post-escape form selection (return as god, new form, or stay outside)
- Central to RIW2's ultimate mystery and gameplay progression

**Event Bus** ([src/core/event_bus.py](src/core/event_bus.py)):
- Central pub/sub for world state changes
- `EventTypes` enum for standardized event kinds (character_action, world_change, etc.)
- Listeners subscribed per event type

**Hot Injection** (`data/inbox/`):
- JSON files placed here are consumed during tick processing
- Patterns: add_character, modify_attribute, inject_event, temporal_anomaly
- Files deleted after processing; workflow: check → parse → validate → apply → remove
- Timeline edits require source energy expenditure

**State Management** ([src/core/state_manager.py](src/core/state_manager.py)):
- Snapshots saved as pickle files in `data/snapshots/`
- Naming: `{world_id}_tick_{number}.pkl`
- Supports rollback to specific tick, branch exploration

## Build and Test

```bash
# Install dependencies
pip install -r requirements.txt

# Run simulation with CLI
python tools/cli.py

# Run with custom configurations
python tools/cli.py --tick-rate 2.0 --world cyberpunk_city

# Custom injections (place JSON in data/inbox/)
# Example: data/inbox/add_neo.json then run simulation
```

## Project Conventions

**File Organization**:
- Config files (`.yaml`) live in `universe/{world_name}/` alongside implementation
- Universal config in `universe/config.yaml` (shared by all worlds)
- Prompt templates stored as separate files in `src/modules/story_mod/prompt_templates/` (not hardcoded)
- World-specific logic as separate module/class per universe, inheriting `BaseWorld`
- Universe lore and cosmology documented in [UNIVERSE_LORE.md](UNIVERSE_LORE.md)

**Entity Lifecycle**:
1. Define shape using `@dataclass Entity` subclasses with type hints
2. Register with world's entity registry
3. Serialize via `.to_dict()` for snapshots and logs
4. Deserialize via `.from_dict()` when loading state
5. Track universal attributes (strength, wisdom, spirit, constitution) shared across all worlds

**Source Energy System**:
- All cross-world operations consume source energy (E/D/C/B/A tiers)
- A-level fragments are rarest and required (7 total) for escape attempt
- Source energy costs defined in `universe/config.yaml` and validated before operations
- Consumption tracked in `UniverseState.source_energy_consumed`

**Escape Protocol**:
- Entities must collect 7 A-level source energy fragments scattered across worlds
- Discover 7 coordinate key clues (hidden in prophecies, constants, genetics, architecture)
- Decrypt master key using collected clues
- Activate terminal gateway (costs 7 A-level fragments)
- Get printed to real universe and achieve transcendence
- Post-escape, choose to return as god, new form, or remain outside

**Event Pattern**:
```python
# Define in EventTypes enum
# Emit via: self.event_bus.publish(Event(type=EventTypes.YOUR_EVENT, data={...}))
# Listen: self.event_bus.subscribe(EventTypes.YOUR_EVENT, handler_function)
# Universal events propagate across all worlds
```

**World Implementation**:
- Extend `BaseWorld` from `universe/base_world.py`
- Implement `tick()`, `serialize()`, `deserialize()`
- Store configuration in `.yaml` (load via PyYAML alongside world implementation)
- Define initial characters/items in `.json` files
- Source energy fragments and key locations defined in global `universe/config.yaml`

## Integration Points

**LLM Client** ([src/utils/llm_client.py](src/utils/llm_client.py)):
- Initialized via `create_llm_client()` factory function
- Supports Gemini API (and extensible to others)
- Used by `Narrator` and `Illustrator`

**Story Generation** ([src/modules/story_mod/narrator.py](src/modules/story_mod/narrator.py)):
- Consumes event logs from `data/logs/`
- Generates narrative via LLM with prompt templates
- Output feeds into `Illustrator` for image generation

**Game Bridge**:
- `src/modules/game_mod/` exports world state as JSON/XML for game engines
- `text_rpg.py` provides console interface for testing interactions

**External APIs**:
- Gemini API (LLM and image generation)
- API keys stored in `.env` file (not committed)

## Security

- **Secrets**: API keys loaded from `.env` using environment variables
- **State Files**: Snapshots in `data/` may contain sensitive world state—do not commit
- **Hot Injection**: Validate and sanitize JSON inputs from `data/inbox/` before applying
- **Log Files**: `data/logs/` may contain PII from character narratives—handle appropriately

## Core Universe Documentation

The RIW2 universe has extensive design documentation that defines mechanics across multiple domains:

**Essential References**:
- [UNIVERSE_LORE.md](UNIVERSE_LORE.md) - Foundational universe mythology and core systems
- [SOURCE_ENERGY.md](SOURCE_ENERGY.md) - Complete economic and resource system (regeneration, decay, tier system)
- [ESCAPE_QUEST.md](ESCAPE_QUEST.md) & [ESCAPE_QUEST_ZH.md](ESCAPE_QUEST_ZH.md) - Game objectives and victory conditions
- [ESCAPE_COMPETITION.md](ESCAPE_COMPETITION.md) - Multi-player competition mechanics, alliance systems, betrayal risks
- [CROSS_WORLD_RULES.md](CROSS_WORLD_RULES.md) - Physics compatibility, ability scaling, time dilation effects
- [SERVER_AI_PROTOCOL.md](SERVER_AI_PROTOCOL.md) - Celestial Core behavior, testing mechanisms, defense systems
- [POST_ESCAPE_INTERACTION.md](POST_ESCAPE_INTERACTION.md) - Godhood powers, divine communication, eternal universe engagement

When implementing features, cross-reference these documents to ensure consistency with established lore.

## Testing Conversions

When adding new features:
1. Write minimal repro in `tools/cli.py` or test script
2. Verify with `pip install -r requirements.txt` environment
3. Test serialization/deserialization round-trip for any new entity types
4. Validate event flow through event bus subscribers
5. Ensure new features align with SOURCE_ENERGY, ESCAPE_COMPETITION, and other universe mechanics
