from chatbot import ask_ai


def chat_loop():
    print("พิมพ์คำถามได้เลย (พิมพ์ exit เพื่อออก, พิมพ์ clear เพื่อล้างความจำ)")

    history = []  # ที่เก็บประวัติแชทของการสนทนานี้

    while True:
        question = input("คุณ: ").strip()

        if question == "exit":
            print("จบการทำงาน")
            break

        if question == "clear":
            history.clear()
            print("ล้างความจำแล้ว")
            continue

        if question == "":
            print("กรุณาพิมพ์คำถาม")
            continue

        answer = ask_ai(question, history)
        print("บอท:", answer)


if __name__ == "__main__":
    chat_loop()