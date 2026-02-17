# 项目目录结构

这个目录结构是为了适配 **VSCode + AI 辅助编程** 的工作流而设计的。它强调模块化、配置化（方便AI读取和生成）以及数据驱动（方便快照和回滚）。

考虑到核心逻辑是“**代码模拟（World）驱动故事（Story）和游戏（Game）**”，我们将采用 **Monorepo（单体仓库）** 结构，以便 AI 能同时理解三个模块的上下文。

### RIW2 项目目录结构推荐

```text
RIW2/
├── .vscode/                   # VSCode 配置
│   ├── settings.json          # 隐藏不必要文件，优化AI搜索范围
│   └── launch.json            # 调试配置（World模拟器、Story生成器）
├── .env                       # API Keys (Gemini, etc.)
├── requirements.txt           # Python依赖库
├── README.md                  # 项目总览（AI读取的首要上下文）
│
├── docs/                      # 文档（核心概念定义，供AI参考）
│   ├── architecture.md        # 架构设计说明
│   ├── api_spec.md            # 模块间接口定义
│   └── world_rules.md         # 世界通用的物理/逻辑规则
│
├── src/                       # 源代码
│   ├── core/                  # [核心引擎层] 通用逻辑，不涉及具体世界内容
│   │   ├── __init__.py
│   │   ├── simulation.py      # 模拟循环 (Tick Loop)
│   │   ├── state_manager.py   # 状态管理 (Save/Load/Snapshot/Rollback)
│   │   ├── event_bus.py       # 事件总线 (处理注入、交互)
│   │   └── entities.py        # 基础实体类 (BaseCharacter, BaseItem)
│   │
│   ├── modules/               # [三大功能模块]
│   │   ├── world_mod/         # World模块：逻辑与模拟
│   │   │   ├── rules.py       # 规则引擎
│   │   │   └── actions.py     # 实体可执行的动作
│   │   ├── story_mod/         # Story模块：叙事生成
│   │   │   ├── narrator.py    # LLM交互层，将Log转为小说
│   │   │   ├── illustrator.py # 文生图接口
│   │   │   └── prompt_templates/ # 存放各类Prompt模板 (.jinja2 or .txt)
│   │   └── game_mod/          # Game模块：游戏数据生成
│   │       ├── unity_bridge/  # 生成供Unity/Godot读取的JSON/XML
│   │       └── text_rpg.py    # 简易控制台版游戏（用于快速测试）
│   │
│   └── utils/                 # 工具库
│       ├── llm_client.py      # 封装Gemini API调用
│       └── logger.py          # 系统日志记录
│
├── universes/                 # [内容层] 具体的小世界定义
│   ├── __init__.py
│   ├── base_world.py          # 世界基类
│   │
│   ├── cyberpunk_city/        # 示例小世界 A
│   │   ├── config.yaml        # 世界设定（重力、经济、初始人口）
│   │   ├── scripts.py         # 该世界特有的逻辑代码
│   │   └── characters.json    # 初始角色池
│   │
│   └── ancient_dynasty/       # 示例小世界 B
│       ├── config.yaml
│       └── ...
│
├── data/                      # [数据层] 运行时数据（Git ignore建议）
│   ├── runtime/               # 当前运行时的内存状态Dump
│   ├── snapshots/             # [核心] 存档点 (Time Machine)
│   │   ├── world_A_tick_100.pkl
│   │   └── world_A_tick_200.pkl
│   ├── logs/                  # 模拟日志 (Story模块的输入源)
│   │   └── simulation.log
│   └── inbox/                 # [热注入通道]
│       └── pending_injections.json # 存放待注入的角色/事件
│
└── tools/                     # [CLI工具] 供你在终端快速操作
    ├── cli.py                 # 主入口
    ├── inject.py              # 快速生成注入文件的脚本
    └── render_story.py        # 手动触发故事生成

```

---

### 关键目录设计意图详解

#### 1. `src/core/` vs `universes/`

* **设计目的**：将“引擎”与“内容”分离。
* **AI 协作点**：当你让 AI 创建一个新的“修仙世界”时，它只需要在 `universes/` 下新建文件夹，并继承 `src/core/` 里的基类。这样无论你有多少个小世界，核心模拟逻辑（如时间流逝、保存机制）只需写一次。

#### 2. `data/inbox/` (热注入机制)

* **设计目的**：实现你提到的“暂停并注入”。
* **工作流**：
1. 你（或玩家）在 `pending_injections.json` 中写入一段 JSON（例如：`{"type": "add_character", "name": "Neo"}`）。
2. `simulation.py` 在每个 Tick 结束时检查这个文件夹。
3. 如果有文件，读取并应用到当前状态，然后删除文件，继续运行。


* **AI 优势**：你可以直接用 Gemini CLI 命令：“帮我生成一个反派注入到 inbox 里”，AI 会直接生成合法的 JSON 文件放入该目录。

#### 3. `src/modules/story_mod/prompt_templates/`

* **设计目的**：结构化管理 Prompt。
* **AI 协作点**：不要把 Prompt 硬编码在 Python 里。将它们存为 `.txt` 或 `.jinja2` 文件。例如 `battle_scene.txt`。
* **内容示例**：
```text
当前世界状态：{{ world_state }}
发生事件：{{ event_log }}
请根据上述逻辑日志，写一段跌宕起伏的武侠风格描写：

```



#### 4. `data/snapshots/` (时间机器)

* **设计目的**：实现“版本控制”。
* **文件格式**：建议使用 `pickle` (Python) 或 `json` (通用) 来序列化整个 World 对象。
* **操作**：文件命名包含 `Tick` (时间戳) 和 `World_ID`，方便随时 Load 回去。

### 针对 VSCode + Gemini 的配置建议

在 `.vscode/settings.json` 中添加以下配置，可以帮助 AI 插件更好地理解你的项目：

```json
{
    "files.exclude": {
        "**/.git": true,
        "**/__pycache__": true,
        "data/snapshots/*": true  // 避免 AI 扫描大量二进制存档文件
    },
    "search.exclude": {
        "data/logs/*": true       // 避免搜索日志文件
    }
}

```

### 你的第一个“Hello World”任务

既然结构已经定好，我建议你的第一步操作是：

1. **创建根目录** 并运行 `mkdir -p src/core src/modules universes data/snapshots`。
2. **让 AI 帮你写 `src/core/simulation.py**` 的骨架代码，要求它包含一个简单的 `while True` 循环，并能每秒打印一次 "Tick"，且能检测 `data/inbox` 里有没有新文件。

你觉得这个结构清晰吗？如果满意，我们可以开始写**第一行代码**（World 核心循环）。