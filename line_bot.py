"""
line_bot.py - ตัวรับ webhook จาก LINE แล้วส่งต่อให้ chatbot.py ตัวเดิม
รันในเครื่อง:  python line_bot.py
รันบนเซิร์ฟเวอร์: gunicorn line_bot:app
"""
import os
import inspect
import logging
import time
from collections import defaultdict, deque

from dotenv import load_dotenv
from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import chatbot  # ตรรกะ AI เดิม (ใช้ข้อมูลชุดเดียวกับเว็บ)

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("line_bot")

CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
CHANNEL_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
if not CHANNEL_SECRET or not CHANNEL_TOKEN:
    raise RuntimeError("ยังไม่ได้ตั้ง LINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN")

app = Flask(__name__)
handler = WebhookHandler(CHANNEL_SECRET)
configuration = Configuration(access_token=CHANNEL_TOKEN)

MAX_HISTORY = getattr(chatbot, "MAX_HISTORY", 10)
MAX_QUESTION_CHARS = getattr(chatbot, "MAX_QUESTION_CHARS", 300)
LINE_TEXT_LIMIT = 4900  # LINE ส่งข้อความได้ไม่เกิน 5000 ตัวอักษร

# ประวัติแชทแยกตามผู้ใช้ (เก็บในหน่วยความจำ จะหายเมื่อเซิร์ฟเวอร์รีสตาร์ต)
histories = {}

# ระบบจำกัดความถี่ (Rate Limiting): จำกัด 6 ข้อความต่อ 1 นาทีต่อคน
hits = defaultdict(deque)
PER_MINUTE = 6

def too_fast(uid):
    now = time.time()
    q = hits[uid]
    
    # ลบประวัติเวลาที่เกิน 1 นาทีออก
    while q and q[0] < now - 60:
        q.popleft()
        
    if len(q) >= PER_MINUTE:
        return True
        
    q.append(now)
    return False


def get_answer(question, history):
    """จุดเดียวที่เชื่อมกับ chatbot.py ถ้าชื่อฟังก์ชัน/พารามิเตอร์ไม่ตรง ให้แก้ที่นี่"""
    params = inspect.signature(chatbot.ask_ai).parameters
    if len(params) >= 2:
        return str(chatbot.ask_ai(question, history))
    return str(chatbot.ask_ai(question))


@app.route("/", methods=["GET"])
def health():
    return "ok"


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)  # ตรวจ signature ว่ามาจาก LINE จริง
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent)
def on_message(event):
    # ข้อความที่ไม่ใช่ตัวอักษร (สติกเกอร์ รูป ฯลฯ)
    if not isinstance(event.message, TextMessageContent):
        reply(event, "ตอนนี้ตอบได้เฉพาะข้อความตัวอักษรนะครับ ลองพิมพ์คำถามเกี่ยวกับวิทยาลัยได้เลย")
        return

    question = (event.message.text or "").strip()
    if not question:
        reply(event, "พิมพ์คำถามที่ต้องการได้เลยครับ")
        return
    if len(question) > MAX_QUESTION_CHARS:
        reply(event, f"คำถามยาวเกินไป ช่วยย่อให้ไม่เกิน {MAX_QUESTION_CHARS} ตัวอักษรนะครับ")
        return

    user_id = getattr(event.source, "user_id", None) or "unknown"

    # เช็กว่าส่งข้อความเร็วเกินกำหนดหรือไม่[cite: 8]
    if too_fast(user_id):
        reply(event, "คุณส่งข้อความเร็วเกินไปครับ กรุณารอสักครู่นแล้วลองใหม่อีกครั้งนะครับ")
        return

    history = histories.setdefault(user_id, [])

    try:
        answer = get_answer(question, history)
    except Exception:
        log.exception("ask_ai ล้มเหลว")
        answer = "ขออภัย ระบบขัดข้องชั่วคราว ลองใหม่อีกครั้งในอีกสักครู่นะครับ"

    # เก็บประวัติเอง เฉพาะกรณีที่ chatbot.py ไม่ได้เก็บไว้ใน history ที่ส่งไป
    if not history or history[-1].get("content") != answer:
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
    del history[:-MAX_HISTORY]

    reply(event, answer)


def reply(event, text):
    text = text[:LINE_TEXT_LIMIT]
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=text)],
            )
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))