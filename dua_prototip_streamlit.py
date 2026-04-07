import streamlit as st
import json
import os
from openai import OpenAI

client = OpenAI()

DATA_FILE = "data.json"



def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}

    if "users" not in data:
        data["users"] = {}
    if "tasks" not in data:
        data["tasks"] = {}
    if "circles" not in data:
        data["circles"] = {}
    if "lessons" not in data:
        data["lessons"] = []
    if "curriculum" not in data:
        data["curriculum"] = {}
    if "progress" not in data:
        data["progress"] = {}

    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()
if "progress" not in data:
    data["progress"] = {}
    save_data(data)


def create_curriculum():
    subjects = ["Türkçe", "Matematik", "Fen", "Tarih"]
    grades = ["5", "6", "7", "8"]

    curriculum = {}

    for grade in grades:
        curriculum[grade] = {}
        for subject in subjects:
            curriculum[grade][subject] = [
                f"{subject} Ünite 1",
                f"{subject} Ünite 2"
            ]
    return curriculum

if not data["curriculum"]:
    data["curriculum"] = create_curriculum()
    save_data(data)



def get_ai_feedback(answers, subject, unit):
    prompt = f"""
    Öğrenci {subject} dersinde {unit} ünitesinde şu cevapları verdi:
    {answers}

    - Hangi konularda zorlanıyor?
    - Hangi alt konular eksik?
    - Kısa ve motive edici geri bildirim ver
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content



if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None

if "current_unit" not in st.session_state:
    st.session_state.current_unit = None



st.title(" Dijital Umut Ağı")



if not st.session_state.logged_in:

    menu = ["Giriş Yap", "Kayıt Ol"]
    choice = st.sidebar.selectbox("Menü", menu)

    if choice == "Kayıt Ol":
        st.subheader("Kayıt Ol")

        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        role = st.selectbox("Rol", ["Öğrenci", "Mentor"])

        if st.button("Kayıt Ol"):
            if username in data["users"]:
                st.warning("Bu kullanıcı zaten var")
            else:
                data["users"][username] = {
                    "password": password,
                    "role": role
                }
                save_data(data)
                st.success("Kayıt başarılı!")

    else:
        st.subheader("Giriş Yap")

        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")

        if st.button("Giriş Yap"):
            if username in data["users"] and data["users"][username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = data["users"][username]["role"]
                st.rerun()
            else:
                st.error("Bilgiler yanlış")

# -------------------
# APP
# -------------------

else:

    username = st.session_state.username
    role = st.session_state.role

    menu = ["Panel", "Dersler", "Gelişim"]
    choice = st.sidebar.selectbox("Menü", menu)

    # -------------------
    # PANEL
    # -------------------

    if choice == "Panel":

        st.subheader(f"Hoş geldin {username}")

        if role == "Öğrenci":
            st.write("Bugün ne öğrenmek istersin?")

        if role == "Mentor":
            st.write("Öğrencilerin gelişimini takip edebilirsin.")

    

    elif choice == "Dersler":

        st.header(" Dersler")

        tab = st.selectbox("Seçim", ["Ders Bul", "Quiz"])

        # -------- DERS BUL --------
        if tab == "Ders Bul":

            grade = str(st.selectbox("Sınıf", [5,6,7,8]))
            subject = st.selectbox("Ders", list(data["curriculum"][grade].keys()))
            unit = st.selectbox("Ünite", data["curriculum"][grade][subject])

            st.subheader(" Dersler")

            for lesson in data["lessons"]:
                if lesson["grade"] == grade and lesson["subject"] == subject and lesson["unit"] == unit:
                    st.write(lesson["title"])
                    st.write(lesson["link"])

                    if st.button(f"Derse Katıl - {lesson['title']}"):
                        st.session_state.current_unit = unit
                        st.success("Ders seçildi")

        
        if tab == "Quiz":

            if not st.session_state.current_unit:
                st.warning("Önce bir ders seç")
            else:
                unit = st.session_state.current_unit
                st.subheader(f"{unit} Quiz")

                q1 = st.radio("Üçgenin iç açılar toplamı?", ["90","180","360"])
                q2 = st.radio("Alan formülü?", ["taban*yükseklik","taban*yükseklik/2"])

                if st.button("Gönder"):

                    answers = {"q1": q1, "q2": q2}

                    feedback = get_ai_feedback(answers, subject, unit)

                    st.subheader(" AI Geri Bildirim")
                    st.write(feedback)

                   
                    if username not in data["progress"]:
                        data["progress"][username] = []

                    data["progress"][username].append({
                        "subject": subject,
                        "unit": unit,
                        "answers": answers,
                        "feedback": feedback
                    })

                    save_data(data)

   

    elif choice == "Gelişim":

        st.header(" Öğrenci Gelişimi")

        if role == "Öğrenci":

            if username in data["progress"]:
                for p in data["progress"][username]:
                    st.write(f" {p['subject']} - {p['unit']}")
                    st.write(f"AI: {p['feedback']}")
                    st.divider()
            else:
                st.write("Henüz veri yok")

        if role == "Mentor":

            student = st.selectbox("Öğrenci seç", list(data["users"].keys()))

            if student in data["progress"]:
                for p in data["progress"][student]:
                    st.write(f"📘 {p['subject']} - {p['unit']}")
                    st.write(p["feedback"])
                    st.divider()
            else:
                st.write("Veri yok")

   

    if role == "Mentor":

        st.sidebar.subheader("Ders Ekle")

        grade = str(st.sidebar.selectbox("Sınıf", [5,6,7,8]))
        subject = st.sidebar.selectbox("Ders", list(data["curriculum"][grade].keys()))
        unit = st.sidebar.selectbox("Ünite", data["curriculum"][grade][subject])
        title = st.sidebar.text_input("Başlık")
        link = st.sidebar.text_input("Link")

        if st.sidebar.button("Ekle"):
            data["lessons"].append({
                "title": title,
                "grade": grade,
                "subject": subject,
                "unit": unit,
                "link": link
            })
            save_data(data)
            st.sidebar.success("Eklendi")
            st.rerun()

   

    if st.sidebar.button("Çıkış Yap"):
        st.session_state.logged_in = False
        st.rerun() 
