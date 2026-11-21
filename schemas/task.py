from pydantic import BaseModel


# --- 2. Pydantic 数据验证模型 ---
class TaskCreate(BaseModel):
    title: str


class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool

    class Config:
        from_attributes = True  # 允许从 ORM 对象读取数据
