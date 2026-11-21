from typing import List

# 3. 导入其它第三方库
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

# 4. 导入本地文件
import models
from database import get_db
from schemas.task import TaskCreate, TaskResponse

router = APIRouter()


@router.get("/tasks", response_model=List[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db)):
    """从数据库获取所有任务"""
    tasks = db.query(models.TaskModel).all()
    return tasks


@router.post("/tasks", response_model=TaskResponse)
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
@router.put("/tasks/{task_id}", response_model=TaskResponse)
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
@router.delete("/tasks/{task_id}")
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
