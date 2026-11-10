# CLI Todo Tool (命令行待办工具)

一个基于 Python 开发的命令行待办事项管理工具，支持任务的添加、查看以及本地 JSON 持久化存储。本项目作为 AI 应用开发基础工程的练习，包含模块化设计、类型提示、异常处理及完整的 Git 工作流。

## ✨ 功能特性
- **添加任务**：支持防呆设计（空输入自动抛出异常）。
- **展示任务**：带状态标识（✔/✘）的列表展示。
- **数据持久化**：自动读取和保存至本地 `tasks.json` 文件。
- **类型提示**：全量 Type Hints 覆盖，保证代码健壮性。

## 🛠️ 技术栈
- Python 3.10+
- 标准库：`json`, `typing`, `os`
- 虚拟环境管理：`venv`

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/KeFan-Z/cli-todo.git
cd cli-todo

python -m venv .venv
# Windows:
source .venv/Scripts/activate
# Mac/Linux:
source .venv/bin/activate

python main.py

cli-todo/
├── main.py            # 程序入口
├── todo_service.py    # 核心业务逻辑（含异常处理与JSON读写）
├── .gitignore         # Git忽略规则
├── LINUX_NOTES.md     # 学习笔记
└── README.md          # 项目说明

