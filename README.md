# RIWA2 (Recursive Interactive World in AI 2.0)

RIWA2 is an AI-driven, community-participatory, evolvable cross-media metaverse engine.

## Project Structure

```
riw2/                          (真实项目根 = 虚拟宇宙的运行容器)
├── docs/                       (项目管理文档)
│   ├── PROJECT.md             项目规划与架构
│   ├── IDEA.md                核心想法与概念
│   └── idea_feedback.md       想法反馈与迭代
│
├── lore/                       (RIWA2宇宙规则文档)
│   ├── README.md              (宇宙文档导航)
│   ├── UNIVERSE_LORE.md       宇宙基础与创世记
│   ├── SOURCE_ENERGY.md       资源经济体系
│   ├── ESCAPE_QUEST.md        逃脱任务指南
│   ├── ESCAPE_COMPETITION.md  多玩家竞争机制
│   ├── CROSS_WORLD_RULES.md   世界兼容性规则
│   ├── SERVER_AI_PROTOCOL.md  服务器AI行为
│   ├── POST_ESCAPE_INTERACTION.md 神与宇宙互动
│   └── REVIEW_CHECKLIST.md    设计完善清单
│
├── src/                        (真实代码实现 - 引擎)
├── universe/                   (RIWA2世界实现 - 虚拟世界代码)
├── realms/                     (RIWA2派生创意产物 - 虚拟世界産出)
│   └── {world_name}/
│       ├── novels/            图文小说/叙事作品
│       ├── games/             游戏产物
│       ├── illustrations/     概念图/原画
│       └── audio/             配乐/音效
├── tools/
├── data/
├── QWEN.md                     (模型指令)
├── GEMINI.md                   (模型指令)
└── README.md                   (这个文件)
```

## 核心理念

**虚拟中的虚拟**：真实的 `riw2` 项目容纳虚拟的 `RIWA2` 宇宙  
- `docs/` = 真实项目文档（关于这个代码库本身）
- `lore/` = 虚拟宇宙文档（RIWA2的设定与规则）
- `src/` = 代码实现（真实的引擎）
- `universe/` = 虚拟世界实现（虚拟世界的代码）
- `realms/` = 派生创意产物（虚拟世界产生的故事、游戏、美术）

[📖 查看完整宇宙设定](lore/README.md)

## Core Modules

- **World**: Logic and simulation engine (Code as Law).
- **Story**: LLM-driven narrator (Log to Story).
- **Game**: Interactive interface (Procedural Generation).

## Getting Started

### Prerequisites

- Python 3.11+

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
