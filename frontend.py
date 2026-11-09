import streamlit as st
import requests

# 定义后端 API 的基础地址
API_URL = "http://127.0.0.1:8000"

# 设置网页标题
st.title("📝 我的 Web 待办清单")

# ================= 1. 添加任务区域 =================
st.subheader("添加新任务")
new_title = st.text_input("任务内容：", placeholder="例如：学习 Streamlit")

if st.button("添加任务"):
    if new_title.strip():
        # 给后端发送 POST 请求
        response = requests.post(f"{API_URL}/tasks", json={"title": new_title})
        if response.status_code == 200:
            st.success("任务添加成功！")
            st.rerun()  # 刷新页面以显示新数据
        else:
            st.error("添加失败，请检查后端是否启动。")
    else:
        st.warning("任务内容不能为空！")

# ================= 2. 展示和操作任务区域 =================
st.divider()
st.subheader("当前任务列表")

# 从后端获取所有任务 (GET 请求)
try:
    response = requests.get(f"{API_URL}/tasks")
    if response.status_code == 200:
        tasks = response.json()  # 拿到 JSON 数据转成 Python 列表

        if not tasks:
            st.info("暂无任务，快去添加一个吧！")

        for task in tasks:
            # 使用 columns 将每一行分成三列：任务名、完成按钮、删除按钮
            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                status = "✅" if task["done"] else "❌"
                st.write(f"{status} **{task['title']}** (ID: {task['id']})")

            with col2:
                # 如果任务未完成，显示“完成”按钮
                if not task["done"]:
                    if st.button("完成", key=f"done_{task['id']}"):
                        # 发送 PUT 请求更新状态
                        requests.put(
                            f"{API_URL}/tasks/{task['id']}",
                            json={"title": task["title"]},
                        )
                        st.rerun()

            with col3:
                # 显示删除按钮
                if st.button("删除", key=f"del_{task['id']}"):
                    # 发送 DELETE 请求
                    requests.delete(f"{API_URL}/tasks/{task['id']}")
                    st.rerun()
    else:
        st.error(f"获取任务失败，状态码：{response.status_code}")
except requests.exceptions.ConnectionError:
    st.error("🔌 无法连接到后端！请确保 uvicorn 正在运行。")
