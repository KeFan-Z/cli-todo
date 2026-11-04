from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# 导入第一周写的服务逻辑
from todo_service import load_tasks, save_tasks, Task

app = FastAPI()


# 定义接收前端数据的模型
class TaskCreate(BaseModel):
    title: str


# 程序启动时，从文件加载数据到内存（注意：这里用全局变量模拟数据库）
# 实际企业开发中，这里会换成数据库查询
my_tasks: List[Task] = load_tasks()


@app.get("/")
def read_root():
    return {"message": "Todo API is running!"}


# 1. 获取所有任务（GET）
@app.get("/tasks", response_model=List[Task])
def get_all_tasks():
    """返回当前所有的任务列表"""
    return my_tasks


# 2. 创建新任务（POST）
@app.post("/tasks", response_model=Task)
def create_new_task(task_in: TaskCreate):
    """接收前端传来的标题，创建任务并保存"""
    try:
        # 调用第一周写的添加逻辑（注意：add_task 接收的是整个任务列表）
        # 我们手动构建任务字典，或者直接调用 add_task 修改 my_tasks 列表
        if not task_in.title.strip():
            raise ValueError("标题不能为空")

        new_task = {"title": task_in.title.strip(), "done": False}
        my_tasks.append(new_task)

        # 关键：每次新增后，必须立即保存到文件，否则重启就丢了
        save_tasks(my_tasks)

        return new_task
    except ValueError as e:
        # 抛出 HTTP 400 错误，告诉前端请求有问题
        raise HTTPException(status_code=400, detail=str(e))
