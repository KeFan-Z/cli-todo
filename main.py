from todo_service import add_task, list_tasks, save_tasks, load_tasks

if __name__ == "__main__":
    my_tasks = load_tasks()
    try:
        add_task("学习 JSON 持久化", my_tasks)
        add_task("完成第 4 天任务", my_tasks)
        # 尝试添加空任务触发异常
        # add_task("", my_tasks)
    except ValueError as e:
        print(f"输入错误：{e}")

    # 2. 打印当前所有任务
    list_tasks(my_tasks)

    # 3. 将最新任务保存回文件
    save_tasks(my_tasks)
