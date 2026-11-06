from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

import models
from database import engine, SessionLocal

# 启动时自动建表（如果表不存在）
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


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
