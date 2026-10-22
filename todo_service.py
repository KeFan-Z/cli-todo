import json

from typing import List, Dict

Task = Dict[str, str | bool]


def add_task(title: str, tasks: List[Task]) -> None:
    """添加任务到列表，如果标题为空则抛出异常"""
    if not title or not title.strip():
        raise ValueError("任务标题不能为空")
    tasks.append({"title": title.strip(), "done": False})


def list_tasks(tasks: List[Task]) -> None:
    """打印所有任务，如果列表为空则提示"""
    if not tasks:
        print("暂无任务")
        return
    for index, task in enumerate(tasks, start=1):
        status = "✔" if task["done"] else "✘"
        print(f"{index}. [{status}] {task['title']}")


if __name__ == "__main__":
    my_tasks = []
    add_task("学习 FastAPI", my_tasks)
    add_task("完成第 2 天任务", my_tasks)
    list_tasks(my_tasks)


def save_tasks(tasks: List[Task], filename: str = "tasks.json") -> None:
    """将任务列表保存到 JSON 文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def load_tasks(filename: str = "tasks.json") -> List[Task]:
    """从 JSON 文件加载任务列表"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果文件不存在（第一次运行），返回空列表
        print("提示：未找到任务文件，将创建新任务列表。")
        return []
