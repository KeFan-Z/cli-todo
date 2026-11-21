import os
import re
import json
from dotenv import load_dotenv

from routers import tasks

# 1. 优先加载环境变量
load_dotenv()
# 2. 设置 HuggingFace 镜像（必须在导入 transformers 之前）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 3. 导入其它第三方库
from fastapi import FastAPI, HTTPException, Depends
from routers import tasks
from sqlalchemy.orm import Session
from openai import OpenAI
import chromadb
from sentence_transformers import SentenceTransformer

# 4. 导入本地文件
import models
from database import engine, get_db
from schemas.chat import ChatRequest, AskRequest, AgentChatRequest
from services.agent_tools import (
    agent_tools,
    list_todo_tasks,
    delete_todo_task_by_title,
    complete_todo_task_by_title,
)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
)


# 启动时自动建表（如果表不存在）
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 模拟数据库，格式：{"user_123": [ {...}, {...} ]}
chat_histories = {}

app.include_router(tasks.router)
app.include_router(tasks.router)

print("正在加载 RAG 模型和向量数据库...")
# 全局加载模型
embed_model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
# 连接之前建好的 ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="my_knowledge")
print("RAG 初始化完成！")


# --- 1. 数据库依赖注入 ---
# # 每次有请求来，就开一个 db 会话；请求结束，自动关闭
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# # --- 2. Pydantic 数据验证模型 ---
# class TaskCreate(BaseModel):
#     title: str


# class TaskResponse(BaseModel):
#     id: int
#     title: str
#     done: bool

#     class Config:
#         from_attributes = True  # 允许从 ORM 对象读取数据


# # --- 3. API 接口 ---
# @app.get("/")
# def read_root():
#     return {"message": "Todo API with Database is running!"}


# @app.get("/tasks", response_model=List[TaskResponse])
# def get_all_tasks(db: Session = Depends(get_db)):
#     """从数据库获取所有任务"""
#     tasks = db.query(models.TaskModel).all()
#     return tasks


# @app.post("/tasks", response_model=TaskResponse)
# def create_new_task(task_in: TaskCreate, db: Session = Depends(get_db)):
#     """将新任务存入数据库"""
#     if not task_in.title.strip():
#         raise HTTPException(status_code=400, detail="标题不能为空")

#     # 创建一个 SQLAlchemy 模型对象
#     new_task = models.TaskModel(title=task_in.title.strip(), done=False)
#     # 写入数据库
#     db.add(new_task)
#     db.commit()
#     # 刷新，为了拿到自增的 ID
#     db.refresh(new_task)

#     return new_task


# # --- 4. 修改任务状态 (PUT) ---
# @app.put("/tasks/{task_id}", response_model=TaskResponse)
# def update_task_status(
#     task_id: int, task_update: TaskCreate, db: Session = Depends(get_db)
# ):
#     # 1. 去数据库里找这个 id 的任务
#     db_task = db.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()

#     # 2. 如果没找到，抛出 404 错误
#     if db_task is None:
#         raise HTTPException(status_code=404, detail="任务不存在")

#     # 3. 更新任务属性（这里我们假设传入的 title 是更新后的内容，这里简单演示将 done 设为 True）
#     # 实际开发中，我们会用一个新的 Pydantic 模型来专门接收更新字段，今天先简化处理
#     db_task.done = True
#     db.commit()
#     db.refresh(db_task)

#     return db_task


# # --- 5. 删除任务 (DELETE) ---
# @app.delete("/tasks/{task_id}")
# def delete_task(task_id: int, db: Session = Depends(get_db)):
#     # 1. 找任务
#     db_task = db.query(models.TaskModel).filter(models.TaskModel.id == task_id).first()

#     # 2. 找不到就 404
#     if db_task is None:
#         raise HTTPException(status_code=404, detail="任务不存在")

#     # 3. 从数据库删除
#     db.delete(db_task)
#     db.commit()

#     return {"message": f"任务 {task_id} 已成功删除"}


# class ChatRequest(BaseModel):
#     session_id: str
#     message: str


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


# class AskRequest(BaseModel):
#     question: str


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


# def list_todo_tasks() -> dict:
#     """查数据库里所有的任务，给 LLM 看。"""
#     db = SessionLocal()
#     try:
#         # ① 把数据库里所有任务查出来
#         tasks = db.query(models.TaskModel).all()
#         # ← 你来写：db.query(models.TaskModel).all()

#         if not tasks:
#             return {"status": "success", "message": "当前没有任何待办任务。"}

#         # ② 把任务对象转成纯文本列表，方便 AI 读懂
#         # 格式类似："ID: 1, 标题: 买牛奶, 状态: 未完成"
#         task_list = []
#         for t in tasks:
#             status = "已完成" if t.done else "未完成"
#             # ← 你来写：把 f"ID: {t.id}, 标题: {t.title}, 状态: {status}" 添加到 task_list 里 (用 append)
#             task_list.append(f"ID: {t.id}, 标题: {t.title}, 状态: {status}")
#         # ③ 把列表用换行符拼成一整段长文本
#         result_text = "\n".join(task_list)
#         return {"status": "success", "tasks": result_text}
#     finally:
#         db.close()


# def delete_todo_task_by_title(title: str) -> dict:
#     """按标题模糊删除一条任务。返回给 LLM 看的 dict。"""
#     db = SessionLocal()
#     try:
#         # ① 查：标题含 title 的第一条
#         task = (
#             db.query(models.TaskModel)
#             .filter(models.TaskModel.title.contains(title))
#             .first()
#         )  # 你来写
#         # ← 你来写：db.query(models.TaskModel).filter(...).first()

#         if not task:
#             return {"status": "error", "message": f"没找到标题包含「{title}」的任务"}

#         # ② 删之前先记住标题！（commit 后对象就过期了，再访问会报错）
#         deleted_title = task.title  # ← 你来写

#         # ③ 删 + 确认
#         db.delete(task)  # ← 你来写
#         db.commit()  # ← 你来写
#         # ← 你来写：db.delete(task)  和  db.commit()

#         return {"status": "success", "message": f"已删除任务：{deleted_title}"}
#     finally:
#         db.close()


# def complete_todo_task_by_title(title: str) -> dict:
#     """按标题模糊把一条任务标记为 done=True。"""
#     db = SessionLocal()
#     try:
#         # ④ 查（同上）
#         task = (
#             db.query(models.TaskModel)
#             .filter(models.TaskModel.title.contains(title))
#             .first()
#         )
#         # ← 你来写

#         if not task:
#             return {"status": "error", "message": f"没找到标题包含「{title}」的任务"}

#         # ⑤ 已经完成过了就别重复操作（可选加分，先写也行）
#         if task.done:
#             return {
#                 "status": "info",
#                 "message": f"任务「{task.title}」本来就是完成状态",
#             }

#         # ⑥ 打勾 + 确认
#         db_task = task  # ← 你来写：task.done = True  和  db.commit()
#         db_task.done = True
#         db.commit()
#         # ← 你来写：task.done = True  和  db.commit()

#         return {"status": "success", "message": f"已把任务「{task.title}」标记为完成"}
#     finally:
#         db.close()


# # 1. 定义工具清单
# agent_tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "add_todo_task",
#             "description": "当用户想要添加一个新的待办事项时，调用此函数。",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "title": {"type": "string", "description": "待办事项的具体内容"}
#                 },
#                 "required": ["title"],
#             },
#         },
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "delete_todo_task",
#             "description": "当用户想删除某个待办事项时调用。需要提供要删除任务的标题或关键词。",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "title": {
#                         "type": "string",
#                         "description": "要删除的任务标题或其中的关键词，例如用户说'删掉买牛奶'就传'买牛奶'",
#                     }
#                 },
#                 "required": ["title"],
#             },
#         },
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "complete_todo_task",
#             "description": "当用户想把某个待办事项标记为已完成时调用。需要提供任务标题或关键词。",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "title": {
#                         "type": "string",
#                         "description": "要标记完成的任务标题或关键词",
#                     }
#                 },
#                 "required": ["title"],
#             },
#         },
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "list_todo_tasks",
#             "description": "查询所有待办事项及其ID。当用户想查看任务列表,或者用户的指令模糊（比如‘把刚才那个删了’、‘打勾开会那个’）时，你必须先调用此工具查看已有任务，然后再决定下一步操作。",
#             "parameters": {
#                 "type": "object",
#                 "properties": {},  # 不需要参数
#             },
#         },
#     },
# ]


# class AgentChatRequest(BaseModel):
#     message: str
#     history: list[dict] = []


def clean_dsml(text: str) -> str:
    """清理 DeepSeek 偶尔抽风吐出来的底层 DSML 标签"""
    if not text:
        return text
    # 正则匹配把 < | | DSML | | 开头的这些乱七八糟的东西全删了
    cleaned = re.sub(r"<.*?DSML.*?>", "", text, flags=re.DOTALL)
    return cleaned.strip()


# 2. Agent 对话接口
@app.post("/agent_chat")
def chat_with_agent(request: AgentChatRequest, db: Session = Depends(get_db)):
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个高效的 AI 待办助手。你可以帮用户查看、添加、删除待办事项，或把待办事项标记为已完成。\n"
                    "重要规则：\n"
                    "1. 必须通过调用工具来操作数据。\n"
                    "2. 删除或完成时，参数名必须是 'title'，不能自己编造其他参数名。\n"
                    "3. 绝对不要输出任何类似 < | | DSML | | > 的底层标签，只输出自然语言或正常调用工具。"
                ),
            }
        ]

        for msg in request.history[-10:]:
            messages.append({"role": msg.get("role"), "content": msg.get("content")})

        messages.append({"role": "user", "content": request.message})

        # 第一次请求，问 AI 要不要用工具
        response = client.chat.completions.create(
            model="deepseek-chat", messages=messages, tools=agent_tools, temperature=0.1
        )

        # 👇 全新的循环引擎开始 👇
        while True:
            response_message = response.choices[0].message

            # 如果 AI 没有调用工具，说明它要正常说话了，退出循环
            if not response_message.tool_calls:
                safe_reply = clean_dsml(response_message.content) or "操作完成！"
                return {"reply": safe_reply}

            # 如果决定调用工具，记录它的意图
            messages.append(response_message)

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name

                # ① 先处理不需要参数的工具
                if function_name == "list_todo_tasks":
                    result = list_todo_tasks()
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )
                    continue  # 查完直接看下一个 tool_call

                # ② 处理需要参数的工具（带防爆拆弹）
                title = None
                try:
                    function_args = json.loads(tool_call.function.arguments)
                    title = function_args.get("title")
                except json.JSONDecodeError:
                    pass

                if not title:
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(
                                {"status": "error", "message": "参数解析失败"},
                                ensure_ascii=False,
                            ),
                        }
                    )
                    continue

                # ③ 分发到对应的执行函数
                if function_name == "add_todo_task":
                    new_task = models.TaskModel(title=title, done=False)
                    db.add(new_task)
                    db.commit()
                    db.refresh(new_task)
                    tool_result = {
                        "status": "success",
                        "message": f"任务 '{title}' 已添加，ID 为 {new_task.id}",
                    }
                elif function_name == "delete_todo_task":
                    tool_result = delete_todo_task_by_title(title)
                elif function_name == "complete_todo_task":
                    tool_result = complete_todo_task_by_title(title)
                elif function_name == "list_todo_tasks":
                    tool_result = list_todo_tasks()
                else:
                    tool_result = {"status": "error", "message": "未知工具"}

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                )

            # 把所有工具的执行结果交还给 AI，继续下一轮请求（千万别忘了带 tools！）
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=agent_tools,
                temperature=0.1,
            )
    except Exception as e:
        print(f"❌ 严重错误：Agent 执行崩溃！报错信息：{e}")
        return {"reply": "老板，我刚刚脑子抽风了，处理失败。请稍后再试一次！"}
