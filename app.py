from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

import models
from database import engine, SessionLocal


import os
from openai import OpenAI
from dotenv import load_dotenv


import os
import chromadb
from sentence_transformers import SentenceTransformer
import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"  # 确保镜像生效


load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
)


# 启动时自动建表（如果表不存在）
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 模拟数据库，格式：{"user_123": [ {...}, {...} ]}
chat_histories = {}


print("正在加载 RAG 模型和向量数据库...")
# 全局加载模型
embed_model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
# 连接之前建好的 ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="my_knowledge")
print("RAG 初始化完成！")


# --- 1. 数据库依赖注入 ---
# 每次有请求来，就开一个 db 会话；请求结束，自动关闭
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 2. Pydantic 数据验证模型 ---
class TaskCreate(BaseModel):
    title: str


class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool

    class Config:
        from_attributes = True  # 允许从 ORM 对象读取数据


# --- 3. API 接口 ---
@app.get("/")
def read_root():
    return {"message": "Todo API with Database is running!"}


@app.get("/tasks", response_model=List[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db)):
    """从数据库获取所有任务"""
    tasks = db.query(models.TaskModel).all()
    return tasks


@app.post("/tasks", response_model=TaskResponse)
def create_new_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    """将新任务存入数据库"""
    if not task_in.title.strip():
        raise HTTPException(status_code=400, detail="标题不能为空")

    # 创建一个 SQLAlchemy 模型对象
    new_task = models.TaskModel(title=task_in.title.strip(), done=False)
    # 写入数据库
    db.add(new_task)
    db.commit()
    # 刷新，为了拿到自增的 ID
    db.refresh(new_task)

    return new_task


# --- 4. 修改任务状态 (PUT) ---
@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task_status(
    task_id: int, task_update: TaskCreate, db: Session = Depends(get_db)
):
    # 1. 去数据库里找这个 id 的任务
    db_task = db.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()

    # 2. 如果没找到，抛出 404 错误
    if db_task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 3. 更新任务属性（这里我们假设传入的 title 是更新后的内容，这里简单演示将 done 设为 True）
    # 实际开发中，我们会用一个新的 Pydantic 模型来专门接收更新字段，今天先简化处理
    db_task.done = True
    db.commit()
    db.refresh(db_task)

    return db_task


# --- 5. 删除任务 (DELETE) ---
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    # 1. 找任务
    db_task = db.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()

    # 2. 找不到就 404
    if db_task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 3. 从数据库删除
    db.delete(db_task)
    db.commit()

    return {"message": f"任务 {task_id} 已成功删除"}


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/chat")
def chat_with_ai(request: ChatRequest):
    # 1. 如果这个会话是新的，初始化它的聊天记录，并设定 AI 的角色 (System Prompt)
    if request.session_id not in chat_histories:
        chat_histories[request.session_id] = [
            {
                "role": "system",
                "content": "你是一个高效的 AI 待办助手。请用简明扼要的中文回答问题。",
            }
        ]

    # 2. 获取该会话的历史记录
    history = chat_histories[request.session_id]

    # 3. 把用户的新消息加入历史
    history.append({"role": "user", "content": request.message})

    try:
        # 4. 把包含历史记录的列表发给大模型
        response = client.chat.completions.create(
            model="deepseek-chat", messages=history
        )

        # 5. 拿到 AI 的回答
        ai_reply = response.choices[0].message.content

        # 6. 把 AI 的回答也加入历史，这样下次它就能看到自己说过什么了
        history.append({"role": "assistant", "content": ai_reply})

        # 7. 返回结果
        return {"reply": ai_reply, "history_length": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AskRequest(BaseModel):
    question: str


@app.post("/ask")
def ask_knowledge_base(request: AskRequest):
    # 1. 把问题向量化
    question_embedding = embed_model.encode([request.question]).tolist()

    # 2. 去 ChromaDB 检索最相关的 2 个片段
    results = collection.query(query_embeddings=question_embedding, n_results=2)
    retrieved_docs = results["documents"][0]
    context = "\n".join(retrieved_docs)

    # 3. 拼接 Prompt
    prompt = f"""你是一个公司内部助手。请严格根据以下【参考材料】回答用户的问题。
    如果参考材料中找不到答案，请直接回答“我不知道，请联系 HR”。
    
    【参考材料】：
    {context}
    
    【用户问题】：{request.question}
    """

    # 4. 调用大模型
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return {
            "reply": response.choices[0].message.content,
            "references": retrieved_docs,  # 顺便把参考依据返回给前端，显得很专业
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
