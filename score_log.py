import sys

# ใช้: python score_log.py test_log_v4.txt
filename = sys.argv[1] if len(sys.argv) > 1 else "test_log_v4.txt"

scores = {}   # {กลุ่ม: {"ถูก": 0, "ผิด": 0, "มั่ว": 0}}
total = {"ถูก": 0, "ผิด": 0, "มั่ว": 0}
ungraded = 0
group = "?"

with open(filename, "r", encoding="utf-8") as file:
    for line in file:
        line = line.strip()
        if line.startswith("กลุ่ม:"):
            group = line.replace("กลุ่ม:", "").strip()
        elif line.startswith("ผล:"):
            result = line.replace("ผล:", "").strip()
            if result in total:
                scores.setdefault(group, {"ถูก": 0, "ผิด": 0, "มั่ว": 0})
                scores[group][result] += 1
                total[result] += 1
            else:
                ungraded += 1  # ยังไม่ได้ตัดสิน

print(f"ไฟล์: {filename}")
for g in sorted(scores):
    s = scores[g]
    print(f"กลุ่ม {g}: ถูก {s['ถูก']}  ผิด {s['ผิด']}  มั่ว {s['มั่ว']}")
print(f"รวม: ถูก {total['ถูก']}  ผิด {total['ผิด']}  มั่ว {total['มั่ว']}")
if ungraded:
    print(f"ยังไม่ได้ตัดสิน {ungraded} ข้อ")