from fastapi import FastAPI
from pydantic import BaseModel


class TaskItem(BaseModel):
    title: str
    done: bool = False


# 创建 FastAPI 实例
app = FastAPI()


# 定义一个 GET 请求的路由（也就是访问路径）
@app.get("/")
def read_root():
    return {"message": "Hello, AI World!"}


# 再定义一个路由
@app.get("/about")
def about():
    return {"project": "cli-todo", "author": "Your Name"}


# 定义一个 POST 请求的路由，用于创建任务
@app.post("/tasks/")
def create_task(task: TaskItem):
    return {"message": "任务创建成功", "received_task": task}
