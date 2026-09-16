# 列表里装字典，这是 AI 应用里处理 JSON 数据最常见的结构
tasks = [{"title": "学习Python", "done": False}, {"title": "配置Git", "done": True}]

# 遍历打印
for task in tasks:
    status = "已完成" if task["done"] else "未完成"
    print(f"任务：{task['title']} | 状态：{status}")
