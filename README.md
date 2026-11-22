# 🚀 全栈 AI 待办应用 (cli-todo)

基于 FastAPI + Streamlit + DeepSeek 构建的智能待办事项管理系统，支持自然语言交互与 Agent 工具调用。

## ✨ 核心功能
- ✅ **基础 CRUD**：任务的增删改查与状态管理。
- 🤖 **智能 Agent**：接入 DeepSeek Function Calling，支持自然语言“帮我加个明天开会的待办”。
- 📚 **RAG 知识库**：基于 ChromaDB + SentenceTransformer，支持本地文档检索问答。
- 🧠 **多轮记忆**：支持上下文对话，Agent 能记住刚才的操作。

## 🛠️ 技术栈
- **后端**：Python 3.10, FastAPI, SQLAlchemy, SQLite
- **前端**：Streamlit
- **AI & 向量**：OpenAI SDK (DeepSeek API), ChromaDB, BGE-Small-Zh

## 🚀 本地运行指南
1. 克隆项目：`git clone ...`
2. 安装依赖：`pip install -r requirements.txt`
3. 配置环境变量：在根目录新建 `.env` 文件，填入 `DEEPSEEK_API_KEY=你的Key`
4. 启动后端：`uvicorn app:app --reload`
5. 启动前端：`streamlit run frontend.py`