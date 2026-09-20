from todo_service import add_task, list_tasks

if __name__ == "__main__":
    my_tasks = []
    try:
        add_task("学习 FastAPI", my_tasks)
        add_task("完成第 3 天任务", my_tasks)
        add_task("", my_tasks)  # 这行会触发 ValueError
    except ValueError as e:
        print(f"输入错误：{e}")

    list_tasks(my_tasks)
