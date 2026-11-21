import models
from database import SessionLocal


def list_todo_tasks() -> dict:
    """查数据库里所有的任务，给 LLM 看。"""
    db = SessionLocal()
    try:
        # ① 把数据库里所有任务查出来
        tasks = db.query(models.TaskModel).all()
        # ← 你来写：db.query(models.TaskModel).all()

        if not tasks:
            return {"status": "success", "message": "当前没有任何待办任务。"}

        # ② 把任务对象转成纯文本列表，方便 AI 读懂
        # 格式类似："ID: 1, 标题: 买牛奶, 状态: 未完成"
        task_list = []
        for t in tasks:
            status = "已完成" if t.done else "未完成"
            # ← 你来写：把 f"ID: {t.id}, 标题: {t.title}, 状态: {status}" 添加到 task_list 里 (用 append)
            task_list.append(f"ID: {t.id}, 标题: {t.title}, 状态: {status}")
        # ③ 把列表用换行符拼成一整段长文本
        result_text = "\n".join(task_list)
        return {"status": "success", "tasks": result_text}
    finally:
        db.close()


def delete_todo_task_by_title(title: str) -> dict:
    """按标题模糊删除一条任务。返回给 LLM 看的 dict。"""
    db = SessionLocal()
    try:
        # ① 查：标题含 title 的第一条
        task = (
            db.query(models.TaskModel)
            .filter(models.TaskModel.title.contains(title))
            .first()
        )  # 你来写
        # ← 你来写：db.query(models.TaskModel).filter(...).first()

        if not task:
            return {"status": "error", "message": f"没找到标题包含「{title}」的任务"}

        # ② 删之前先记住标题！（commit 后对象就过期了，再访问会报错）
        deleted_title = task.title  # ← 你来写

        # ③ 删 + 确认
        db.delete(task)  # ← 你来写
        db.commit()  # ← 你来写
        # ← 你来写：db.delete(task)  和  db.commit()

        return {"status": "success", "message": f"已删除任务：{deleted_title}"}
    finally:
        db.close()


def complete_todo_task_by_title(title: str) -> dict:
    """按标题模糊把一条任务标记为 done=True。"""
    db = SessionLocal()
    try:
        # ④ 查（同上）
        task = (
            db.query(models.TaskModel)
            .filter(models.TaskModel.title.contains(title))
            .first()
        )
        # ← 你来写

        if not task:
            return {"status": "error", "message": f"没找到标题包含「{title}」的任务"}

        # ⑤ 已经完成过了就别重复操作（可选加分，先写也行）
        if task.done:
            return {
                "status": "info",
                "message": f"任务「{task.title}」本来就是完成状态",
            }

        # ⑥ 打勾 + 确认
        db_task = task  # ← 你来写：task.done = True  和  db.commit()
        db_task.done = True
        db.commit()
        # ← 你来写：task.done = True  和  db.commit()

        return {"status": "success", "message": f"已把任务「{task.title}」标记为完成"}
    finally:
        db.close()


# 1. 定义工具清单
agent_tools = [
    {
        "type": "function",
        "function": {
            "name": "add_todo_task",
            "description": "当用户想要添加一个新的待办事项时，调用此函数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "待办事项的具体内容"}
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_todo_task",
            "description": "当用户想删除某个待办事项时调用。需要提供要删除任务的标题或关键词。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "要删除的任务标题或其中的关键词，例如用户说'删掉买牛奶'就传'买牛奶'",
                    }
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_todo_task",
            "description": "当用户想把某个待办事项标记为已完成时调用。需要提供任务标题或关键词。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "要标记完成的任务标题或关键词",
                    }
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_todo_tasks",
            "description": "查询所有待办事项及其ID。当用户想查看任务列表,或者用户的指令模糊（比如‘把刚才那个删了’、‘打勾开会那个’）时，你必须先调用此工具查看已有任务，然后再决定下一步操作。",
            "parameters": {
                "type": "object",
                "properties": {},  # 不需要参数
            },
        },
    },
]
