# 📝 Web CLI Todo Tool (全栈待办应用)

一个基于前后端分离架构的待办事项应用。后端采用 FastAPI + SQLAlchemy 构建 RESTful API，前端采用 Streamlit 极简框架实现交互界面。本项目作为 AI 应用开发的基础工程练习，涵盖了从数据库设计、API 开发到前后端联调的完整开发流程。

## ✨ 功能特性
- **后端 API (FastAPI)**：实现任务的增（POST）、查（GET）、改（PUT）、删（DELETE）完整 CRUD 操作。
- **数据持久化 (SQLAlchemy)**：使用 ORM 框架操作 SQLite 数据库，数据层与业务层解耦。
- **数据校验 (Pydantic)**：严格校验前端传入的数据，自动拦截异常请求。
- **前端界面 (Streamlit)**：提供直观的 Web 界面，支持输入、状态切换和删除操作。
- **异常处理**：全局处理 404 任务不存在及 400 无效输入等错误。

## 🛠️ 技术栈
- **后端**：Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, SQLite
- **前端**：Streamlit, Requests
- **工具**：Git, venv

## 📁 目录结构
```text
cli-todo/
├── app.py               # FastAPI 后端路由与接口
├── database.py          # SQLAlchemy 数据库连接配置
├── models.py            # ORM 数据库表结构定义
├── frontend.py          # Streamlit 前端界面代码
├── .gitignore           # Git 忽略规则（忽略虚拟环境与数据库文件）
└── README.md            # 项目说明文档


🚀 快速开始
1. 克隆项目并安装依赖
git clone https://github.com/KeFan-Z/cli-todo.git
cd cli-todo
python -m venv .venv
# Windows 激活:
source .venv/Scripts/activate
# Mac/Linux 激活:
# source .venv/bin/activate

pip install fastapi uvicorn sqlalchemy streamlit requests

2. 启动后端服务 (终端 A)
uvicorn app:app --reload
后端 API 文档地址：http://127.0.0.1:8000/docs


3. 启动前端界面 (终端 B)
注意：需新开一个终端，同样激活虚拟环境后运行
streamlit run frontend.py
前端访问地址：http://localhost:8501

