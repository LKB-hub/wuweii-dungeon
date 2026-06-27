# 无畏 · Wuweii Dungeon

> 元气骑士风格 Roguelike 地牢冒险游戏，基于 Pygame 开发。

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue" alt="Python">
  <img src="https://img.shields.io/badge/Pygame-2.6.1-green" alt="Pygame">
  <img src="https://img.shields.io/badge/Genre-Roguelike-orange" alt="Genre">
</p>

## 🎮 游戏简介

在随机生成的地牢中探索，拾取武器，击败敌人，挑战Boss。每次冒险都是全新的体验。

## ✨ 核心特性

- **程序化地图** — 随机房间布局，每次进入都是不同地牢
- **6 名可选角色** — 骑士、游侠、法师、刺客、圣骑士、工程师，各有专属技能与被动
- **15 种敌人 + 4 个 Boss** — 从近卫兵、自爆兵到宝箱怪、幽灵，每种 AI 行为各异
- **27+ 武器** — 近战/远程/魔法，附带稀有度系统（普通→传说）
- **主动技能** — 每角色专属大招，冷却管理是制胜关键
- **宠物系统** — 火焰幼龙、治愈精灵、暗影猫等，可升级进化（T 键喂食）
- **经验球磁铁** — 击杀掉落经验球，自动吸附，累积升级
- **武器双持** — 两槽位自由切换，F 键拾取管理
- **闪避翻滚** — 无敌帧躲避攻击，精准操作
- **小地图** — Tab 键查看当前楼层布局
- **成就系统** — 10+ 成就追踪，挑战自我
- **存档系统** — Hub 场景自动加载/存档，ESC 暂停保存
- **开发者模式** — F8 + 输入 88888 开启调试功能

## 🎯 操作指南

| 按键 | 功能 |
|------|------|
| `WASD` | 移动 |
| `鼠标左键` | 攻击 |
| `空格` | 闪避/翻滚 |
| `Q` | 切换武器 |
| `E` | 释放技能 |
| `R` | 换弹 |
| `F` | 拾取武器/交互 |
| `T` | 喂食宠物 |
| `TAB` | 小地图 |
| `P` | 暂停 |
| `ESC` | 菜单/返回 |

## 🗺️ 角色

| 角色 | 特色 | 技能 | 初始武器 |
|------|------|------|---------|
| 骑士 | 高生命，护盾坚韧 | 盾击 | 长剑 |
| 游侠 | 暴击率高，移速快 | 箭雨 | 弓 |
| 法师 | 低生命，高伤害 | 雷暴 | 法杖 |
| 刺客 | 最高移速，背刺 | 暗影步 | 匕首 |
| 圣骑士 | 攻守兼备，治愈 | 神圣之光 | 锤 |
| 工程师 | 召唤炮台，高能量 | 部署炮台 | 霰弹枪 |

## 🏗️ 项目结构

```
无畏/
├── main.py              # 游戏入口
├── settings.py           # 全局配置
├── README.md
├── assets/               # 素材资源
│   ├── characters/       # 角色精灵 (44文件)
│   ├── tiles/            # 地砖精灵 (471文件)
│   ├── tileset/          # DCSS 怪物图集 (数千文件)
│   ├── kenney_dungeon/   # Kenney 地牢素材
│   └── kenney_micro/     # Kenney 微缩素材
├── src/                  # 源代码
│   ├── engine/           # 引擎层
│   │   ├── game.py       # 主循环/场景管理
│   │   ├── scene.py      # 场景基类
│   │   ├── camera.py     # 摄像机系统
│   │   ├── save.py       # 存档读写
│   │   ├── resource.py   # 资源加载
│   │   ├── sound.py      # 音效管理
│   │   ├── font_helper.py# 字体工具
│   │   └── achievements.py# 成就系统
│   ├── entities/         # 实体层
│   │   ├── player.py     # 玩家
│   │   ├── enemy.py      # 敌人 AI
│   │   ├── boss_ai.py    # Boss 行为
│   │   ├── bullet.py     # 子弹/攻击系统
│   │   ├── weapon.py     # 武器系统
│   │   ├── skills.py     # 技能系统
│   │   ├── character.py  # 数据定义
│   │   ├── item.py       # 道具
│   │   ├── inventory.py  # 背包
│   │   ├── pet.py        # 宠物
│   │   ├── particle.py   # 粒子特效
│   │   ├── effects.py    # 视觉效果
│   │   ├── quest.py      # 任务系统
│   │   ├── shop.py       # 商店
│   │   └── weapon_drop.py# 武器掉落
│   ├── ui/               # UI 层
│   │   ├── menu.py       # 主菜单
│   │   ├── hub.py        # 大厅场景
│   │   ├── gameplay.py   # 核心对战 (1588行)
│   │   ├── hud.py        # 抬头显示
│   │   ├── character_select.py# 角色选择
│   │   ├── gameover.py   # 结束画面
│   │   ├── settings_menu.py# 设置菜单
│   │   ├── save_manager.py# 存档管理
│   │   └── minimap.py    # 小地图
│   └── world/            # 世界层
│       ├── dungeon.py    # 地牢生成
│       ├── room.py       # 房间管理
│       └── tile.py       # 地砖系统
├── tools/                # 开发工具脚本
├── memory/               # 开发日志
└── logs/                 # 错误日志
```

## 🚀 运行

```bash
# 安装依赖
pip install pygame

# 启动游戏
python main.py

# 可选启动参数
python main.py --debug      # 调试模式
python main.py --fullscreen # 全屏
python main.py --nosound    # 静音
```

## 📋 需求

- Python 3.12+
- Pygame 2.6.1

## 📝 License

MIT
