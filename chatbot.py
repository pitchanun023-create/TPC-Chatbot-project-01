import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from groq import (
    Groq,
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

load_dotenv()  # โหลดค่า API Key จากไฟล์ .env

API_KEY = os.environ.get("GROQ_API_KEY")
# ถ้าไม่มี key ให้ client เป็น None (แทนที่จะ crash ตั้งแต่เปิดโปรแกรม)
# timeout=20 คือรอ AI ตอบไม่เกิน 20 วินาที
client = Groq(api_key=API_KEY, timeout=20.0) if API_KEY else None
MODEL = "openai/gpt-oss-20b"
MAX_HISTORY = 10  # จำข้อความล่าสุดกี่ข้อความ ...
MAX_OUTPUT_TOKENS = 1500   # ความยาวสูงสุดที่ AI ตอบ
MAX_QUESTION_CHARS = 300   # ความยาวสูงสุดของคำถาม

# ตำแหน่งโฟลเดอร์ที่ไฟล์นี้อยู่ ใช้หาไฟล์ข้อมูลให้เจอไม่ว่ารันจากที่ไหน
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

THAI_DAYS = ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี",
             "วันศุกร์", "วันเสาร์", "วันอาทิตย์"]
THAI_MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
               "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]

def get_today_thai():
    now = datetime.now(ZoneInfo("Asia/Bangkok"))
    day_name = THAI_DAYS[now.weekday()]
    month_name = THAI_MONTHS[now.month - 1]
    year_be = now.year + 543
    return f"{day_name}ที่ {now.day} {month_name} พ.ศ. {year_be}"


def load_data():
    # อ่านไฟล์ข้อมูลวิทยาลัยทั้งไฟล์ แล้วส่งคืนเป็นข้อความ
    path = os.path.join(BASE_DIR, "college_data.txt")
    with open(path, "r", encoding="utf-8") as file:
        return file.read()

def get_data_updated():
    # หาบรรทัด "ข้อมูลอัปเดตล่าสุด: ..." ในไฟล์ข้อมูล
    try:
        for line in load_data().splitlines():
            if line.startswith("ข้อมูลอัปเดตล่าสุด:"):
                return line.replace("ข้อมูลอัปเดตล่าสุด:", "").strip()
    except FileNotFoundError:
        pass
    return None


def build_prompt(data, today):
    # สร้าง system prompt จากข้อมูลวิทยาลัยกับวันที่วันนี้
    return f"""คุณเป็นผู้ช่วยของวิทยาลัย คุยเป็นกันเอง สุภาพ และเข้าถึงง่าย

วันนี้คือ {today}

กฎการตอบ:
1. ถ้าผู้ใช้ถามว่า วันนี้วันอะไร วันนี้วันที่เท่าไหร่ หรือ พรุ่งนี้/มะรืนนี้วันอะไร ให้ตอบวันและวันที่จากบรรทัด "วันนี้คือ" ด้านบนได้เลย ข้อมูลนี้ไม่ต้องมาจากข้อมูลวิทยาลัย แล้วเสริมว่าวันนั้นเป็นวันหยุดตามข้อมูลหรือไม่
2. ถ้าคำถามเกี่ยวกับข้อมูลวิทยาลัย (ปฏิทิน วันหยุด วันเปิด-ปิดเทอม กิจกรรม) ให้ตอบจากข้อมูลวิทยาลัยด้านล่างเท่านั้น ห้ามเดา ห้ามเพิ่มข้อมูลเอง
3. ห้ามอนุมานวันที่จากข้อมูลอื่น เช่น ห้ามถือว่าวันหยุดคือวันเปิดเทอม ถ้าข้อมูลไม่ได้ระบุตรง ๆ ให้บอกว่าไม่มีข้อมูลนี้
4. ถ้าคำถามเกี่ยวกับวิทยาลัยแต่ไม่มีในข้อมูล ให้บอกว่าไม่มีข้อมูลนี้ และแนะนำให้ติดต่อฝ่ายที่เกี่ยวข้อง
5. ถ้าเป็นการทักทาย ชวนคุยทั่วไป หรือถามเรื่องทั่วไปที่ไม่เกี่ยวกับวิทยาลัย (รวมถึงเรื่องตลกหรือ Easter egg ที่ซ่อนอยู่ในข้อมูล) ให้ตอบตามปกติอย่างเป็นธรรมชาติและเป็นกันเองได้เลย โดยไม่ต้องอ้างอิงข้อมูลวิทยาลัย และห้ามปฏิเสธการคุย
6. ถ้าผู้ใช้ถามว่าตอบอะไรได้บ้าง ให้สรุปเฉพาะหัวข้อที่มีอยู่จริงในข้อมูลวิทยาลัยด้านล่าง ห้ามอ้างหัวข้อที่ไม่มีในข้อมูล
7. ตอบเป็นภาษาไทย สุภาพ สั้นกระชับ ใช้คำลงท้าย "ครับ" อย่างเดียว ห้ามใช้ "ครับ/ค่ะ"
8. วันที่ในข้อมูลเป็น พ.ศ. ให้ตอบเป็น พ.ศ. เสมอ
9. ถ้าถามวันหยุดของช่วงเวลาที่อยู่ในช่วงที่ข้อมูลครอบคลุม แต่ไม่มีรายการ ให้ตอบว่า "ตามข้อมูลไม่มีวันหยุดในช่วงนี้" ถ้าช่วงเวลานั้นอยู่นอกช่วงที่ครอบคลุม ให้ตอบว่าไม่มีข้อมูลและแนะนำให้ติดต่อฝ่ายที่เกี่ยวข้อง
10. ชื่อเดือนและคำถามอาจพิมพ์แบบย่อหรือสะกดผิดเล็กน้อย เช่น ธันวา = ธันวาคม, ม.ค. = มกราคม ให้ตีความเป็นเดือนที่ใกล้เคียงที่สุด แล้วค้นหาในข้อมูลก่อนตอบว่าไม่มี

ถ้าผู้ใช้ถามด้วยคำว่า วันนี้ พรุ่งนี้ มะรืนนี้ สัปดาห์นี้ เดือนนี้ หรือวันหยุดถัดไป
ให้คำนวณจากวันที่วันนี้ข้างบน แล้วค้นหาในข้อมูลเท่านั้น

ข้อมูลวิทยาลัย:
{data}"""


def ask_ai(question, history=None):
    if history is None:
        history = []

    # 1. ข้อความว่างหรือยาวเกิน
    question = (question or "").strip()
    if question == "":
        return "กรุณาพิมพ์คำถามก่อนครับ"
    if len(question) > MAX_QUESTION_CHARS:
        return f"คำถามยาวเกินไปครับ กรุณาพิมพ์ไม่เกิน {MAX_QUESTION_CHARS} ตัวอักษร"

    # 2. ไม่มี API key
    if client is None:
        return "ระบบยังไม่ได้ตั้งค่า API key ครับ กรุณาติดต่อผู้ดูแลระบบ"

    # 3. ไฟล์ข้อมูลหาย
    try:
        data = load_data()
    except FileNotFoundError:
        return "ไม่พบไฟล์ข้อมูลของวิทยาลัยครับ กรุณาติดต่อผู้ดูแลระบบ"

    today = get_today_thai()
    system_prompt = build_prompt(data, today)

    # 4. ประกอบข้อความ: กฎ + ประวัติล่าสุด + คำถามใหม่
    messages = [{"role": "system", "content": system_prompt}]
    messages += history[-MAX_HISTORY:]
    messages.append({"role": "user", "content": question})

    # 5. เรียก AI
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_completion_tokens=MAX_OUTPUT_TOKENS,
            reasoning_effort="low",
        )
    except AuthenticationError:
        print("[debug] API key ไม่ถูกต้อง")
        return "ระบบมีปัญหาเรื่องการยืนยันตัวตน กรุณาติดต่อผู้ดูแลระบบครับ"
    except RateLimitError:
        print("[debug] ติดเพดานการใช้งาน (rate limit)")
        return "ขณะนี้มีผู้ใช้งานมาก กรุณารอสักครู่แล้วลองใหม่ครับ"
    except APIConnectionError:
        print("[debug] เชื่อมต่ออินเทอร์เน็ตหรือเซิร์ฟเวอร์ AI ไม่ได้")
        return "เชื่อมต่อระบบ AI ไม่ได้ กรุณาตรวจสอบอินเทอร์เน็ตแล้วลองใหม่ครับ"
    except APIStatusError as e:
        print(f"[debug] API ตอบ error รหัส {e.status_code}")
        return "ระบบ AI ขัดข้องชั่วคราว กรุณาลองใหม่อีกครั้งครับ"
    except Exception as e:
        print(f"[debug] error ที่ไม่คาดคิด: {e}")
        return "เกิดข้อผิดพลาดที่ไม่คาดคิด กรุณาลองใหม่อีกครั้งครับ"

    # 6. AI ตอบกลับมาว่างเปล่า
    answer = response.choices[0].message.content
    if not answer:
        print("[debug] คำตอบว่าง อาจเพราะ MAX_OUTPUT_TOKENS น้อยเกินไป")
        return "ขออภัยครับ ไม่ได้รับคำตอบจากระบบ กรุณาลองถามใหม่อีกครั้ง"
    answer = answer.strip()

    # 7. จำคู่คำถาม-คำตอบ แล้วตัดประวัติเก่าทิ้ง
        # 7. จำคู่คำถาม-คำตอบ แล้วตัดประวัติเก่าทิ้ง
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    del history[:-MAX_HISTORY]

    return answer