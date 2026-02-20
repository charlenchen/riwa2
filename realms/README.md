# RIWA2 派生创意产物库

*虚拟宇宙产生的故事、游戏、美术和其他创意产出*

这个目录存放从 RIWA2 虚拟宇宙中衍生出来的所有创意产物。

## 📂 结构组织

```
realms/
├── {world_name}/              (每个虚拟世界)
│   ├── novels/                图文小说、叙事作品
│   │   ├── chapter_1.md
│   │   ├── chapter_2.md
│   │   └── illustrations/     配套插图
│   ├── games/                 游戏产物
│   │   ├── web/               Web游戏
│   │   ├── mobile/            手机游戏
│   │   ├── vr/                VR体验
│   │   └── game_specs.md      游戏设计文档
│   ├── illustrations/         原画、概念图、世界观美术
│   ├── audio/                 配乐、音效、原声带
│   └── README.md              该世界的创意产物总览
└── shared/                    跨世界的共享资源
    ├── UI_components/         通用UI组件
    ├── music/                 背景音乐库
    └── common_assets/         通用资源
```

## 🎨 内容示例

### novels/ - 叙事产物
- `.md` 文件：章节内容、故事脚本
- `illustrations/` 子目录：章节配图、插画
- `metadata.yaml`：故事元数据（作者、进度、链接到lore文档）

### games/ - 游戏产物
- 各个平台的游戏实现
- `game_specs.md`：游戏规则、玩法、与RIWA2宇宙的映射
- 资源文件：地图、模型、动画等

### illustrations/ - 美术产物
- 世界设定图、角色设计、建筑概念图
- 美术风格指南
- 概念美术探索草稿

### audio/ - 音乐产物
- 世界主题音乐
- 环境音效库
- 角色BGM

## 🔗 与其他目录的关系

- **lore/** → `realms/` 
  - 宇宙规则（lore）指导创意产出（realms）
  - 例如：`UNIVERSE_LORE.md` 的世界设定 → `realms/{world_name}/` 的故事和美术

- **universe/** → `realms/`
  - 世界代码实现（universe）可自动生成或导出内容到 realms
  - 例如：NPC对话生成、游戏关卡导出

- **src/** → `realms/`
  - 引擎功能支持创意产物的生成
  - 例如：故事模块生成小说，游戏模块导出游戏资源

## 📝 创意产物的生命周期

```
设定 (lore/) 
  ↓
代码实现 (universe/ + src/) 
  ↓
自动生成/手工创作 
  ↓
创意产物 (realms/)
  ↓
发布/展示/反馈
```

## 🌟 开始创建

当你为某个世界创建派生产物时：

1. 在 `realms/` 下创建 `{world_name}/` 目录
2. 按需创建 `novels/`、`games/`、`illustrations/`、`audio/` 等子目录
3. 为该世界创建 `README.md` 说明其创意产物迭代状况
4. 在产物中留下对 `lore/` 的链接，说明其在RIWA2宇宙中的位置

---

*创意产物是虚拟宇宙的视觉化和叙事化表达*
