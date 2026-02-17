# RIW2 (Recursive Interactive World 2.0)

RIW2 is an AI-driven, community-participatory, evolvable cross-media metaverse engine.

## Core Modules

- **World**: Logic and simulation engine (Code as Law).
- **Story**: LLM-driven narrator (Log to Story).
- **Game**: Interactive interface (Procedural Generation).

## Getting Started

### Prerequisites

- Python 3.8+

### Installation

```bash
pip install -r requirements.txt
```

### Running the Simulation

```bash
python tools/cli.py
```

### Hot Injection

Place a `.json` file in `data/inbox/` to inject characters or events into the running simulation.
Example injection:
```json
{
    "type": "add_character",
    "name": "Neo",
    "attributes": {"power": 100}
}
```
