from typing import List, Dict

Task = Dict[str, str | bool]


def add_task(title: str, tasks: List[Task]) -> None:
    """添加任务到列表"""
    tasks.append({"title": title, "done": False})


def list_tasks(tasks: List[Task]) -> None:
    """打印所有任务列表"""
    for index, task in enumerate(tasks, start=1):
        status = "✔️" if task["done"] else "❌"
        print(f"{index}. [{status}] {task['title']}")


if __name__ == "__main__":
    my_tasks = []
    add_task("学习 FastAPI", my_tasks)
    add_task("完成第 2 天任务", my_tasks)
    list_tasks(my_tasks)
