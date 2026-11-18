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


st.divider()
st.subheader("📚 公司知识库 AI 助手")

# 使用表单，防止用户输入时频繁刷新页面
with st.form("qa_form"):
    question = st.text_input("请输入你想问的问题：", placeholder="例如：年假有几天？")
    submitted = st.form_submit_button("提问")

if submitted and question:
    with st.spinner("AI 正在翻找手册..."):
        try:
            # 发给后端的 /ask 接口
            res = requests.post(f"{API_URL}/ask", json={"question": question})
            if res.status_code == 200:
                data = res.json()
                st.success("🤖 AI 回答：")
                st.write(data["reply"])

                # 把检索到的参考材料放在折叠面板里
                with st.expander("🔍 查看检索到的参考材料"):
                    for doc in data["references"]:
                        st.info(doc)
            else:
                st.error("后端出错了。")
        except Exception as e:
            st.error(f"连接失败：{e}")


st.divider()
st.subheader("🤖 AI 智能待办助手")
st.write("你可以直接对 AI 说：'帮我看看我有哪些任务'")

# 初始化历史记录（像一个不随刷新消失的袋子）
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 1. 无论刷不刷新，先把袋子里的历史对话画在页面上
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 2. 输入框
agent_prompt = st.chat_input("向 AI 发号施令...")

if agent_prompt:
    # 用户说的话，立刻放进袋子，并画出来
    st.session_state.chat_history.append({"role": "user", "content": agent_prompt})
    with st.chat_message("user"):
        st.write(agent_prompt)

    with st.spinner("AI 正在思考并操作数据库..."):
        try:
            res = requests.post(f"{API_URL}/agent_chat", json={"message": agent_prompt})
            if res.status_code == 200:
                ai_reply = res.json()["reply"]
                # AI 的回复，也放进袋子
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": ai_reply}
                )
                # 刷新页面（这样上面的任务列表会更新，同时对话也不会消失了）
                st.rerun()
            else:
                st.error("后端出错了。")
        except Exception as e:
            st.error(f"连接失败：{e}")
