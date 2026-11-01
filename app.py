import streamlit as st
from chatbot import ask_ai, get_data_updated

# ===== ตั้งค่าที่แก้ได้ที่เดียว =====
COLLEGE_NAME = "<<ใส่ชื่อวิทยาลัย>>"
EXAMPLES = [
    "วันนี้วันอะไร",
    "วันหยุดถัดไปคือวันอะไร",
    "เดือนนี้มีวันหยุดอะไรบ้าง",
    "เดือนหน้ามีวันหยุดอะไรบ้าง",
]
DISCLAIMER = "ข้อมูลอาจคลาดเคลื่อน โปรดตรวจสอบกับฝ่ายที่เกี่ยวข้อง"
MAX_QUESTIONS_PER_SESSION = 30  # จำนวนคำถามสูงสุดต่อการเปิดเว็บหนึ่งครั้ง

st.set_page_config(page_title=f"แชทบอท {COLLEGE_NAME}")
st.title(f"แชทบอท {COLLEGE_NAME}")
st.caption("ถามเรื่องปฏิทินการศึกษา วันหยุด และกิจกรรมของวิทยาลัยได้ที่นี่")

updated = get_data_updated()
if updated:
    st.caption(f"ข้อมูลล่าสุดเมื่อ {updated}")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "pending" not in st.session_state:
    st.session_state.pending = None
if "count" not in st.session_state:
    st.session_state.count = 0


def set_pending(text):
    st.session_state.pending = text


with st.sidebar:
    if st.button("เริ่มแชทใหม่"):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.pending = None
        st.session_state.count = 0
        st.rerun()
    st.caption(DISCLAIMER)

typed = st.chat_input("พิมพ์คำถามที่นี่...")
question = typed or st.session_state.pending
st.session_state.pending = None

if not st.session_state.messages and not question:
    st.write("ลองถามตัวอย่างเหล่านี้ได้เลย:")
    cols = st.columns(2)
    for i, text in enumerate(EXAMPLES):
        cols[i % 2].button(text, key=f"example_{i}", on_click=set_pending, args=(text,))

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if question:
    if st.session_state.count >= MAX_QUESTIONS_PER_SESSION:
        st.warning("ถามครบจำนวนที่กำหนดในรอบนี้แล้วครับ กด 'เริ่มแชทใหม่' ที่แถบข้างเพื่อถามต่อ")
    else:
        st.session_state.count += 1
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("กำลังหาคำตอบ..."):
                answer = ask_ai(question, st.session_state.history)
            st.write(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})

st.caption(DISCLAIMER)