# 国际数棋 (International Number Chess)

一个基于Pygame开发的国际数棋游戏，支持多种游戏模式和功能。

## 功能特性

### 游戏模式
- **对战模式 (Play)**: 双人对战游戏
- **复盘模式 (Replay)**: 回放已保存的游戏记录
- **练习模式 (Practice)**: 关卡挑战系统，包含4个练习关卡
- **自定义摆棋 (Custom Setup)**: 自定义棋子初始位置

### 主要功能
- 完整的游戏记录和回放系统
- 关卡系统，支持不同的胜利条件
- 练习进度记录和管理
- 自定义棋谱保存和加载
- 计算板功能，支持算式输入和验证
- 连续跨越和多路径移动
- 上帝模式（调试用）

## 系统要求

- Python 3.x
- Pygame库

## 安装和运行

1. 确保已安装Python和Pygame：
```bash
pip install pygame
```

2. 运行游戏：
```bash
python test.py
```

## 游戏规则

- 蓝方先手，红方后手
- 棋子可以进行单步移动或跨越移动
- 跨越移动时会获得被跨越棋子的数值
- 不同关卡有不同的胜利条件

## 文件结构
├── test.py                 # 主程序文件
├── levels_config.json      # 关卡配置文件
├── practice_progress.json  # 练习进度记录
├── custom_setups/          # 自定义棋谱目录
│   ├── continous_span.json
│   ├── jump.json
│   ├── move.json
│   └── span.json
└── game_records/           # 游戏记录目录
├── custom_names.json
└── *.json             # 游戏记录文件


## 操作说明

### 基本操作
- 鼠标点击选择棋子
- 点击有效位置移动棋子
- 数字键0-9快速选择对应编号的棋子

### 复盘模式
- 使用播放/暂停按钮控制回放
- 调整播放速度
- 前进/后退按钮逐步查看

### 练习模式
- 选择关卡进行挑战
- 查看关卡提示和目标
- 重置练习进度功能

## 开发信息

- 开发语言: Python
- 图形库: Pygame
- 支持的操作系统: Windows, macOS, Linux

---

*这是一个教育性质的数棋游戏项目，旨在提供完整的游戏体验和学习功能。*