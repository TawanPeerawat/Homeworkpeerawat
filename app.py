import streamlit as st
import pandas as pd
import google.generativeai as genai

# ตั้งค่า Gemini API Key
try:
    key = st.secrets['gemini_api_key']  # อ่านจาก secrets.toml ใน .streamlit/
    genai.configure(api_key=AIzaSyDhcBaFpk3YqRJtb6kLfQhbJSnGoklha8o)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
except Exception as e:
    st.error(f'Failed to configure Gemini API: {e}')
    st.stop()

# ตั้งชื่อแอป
st.title("AI Chatbot + CSV Analysis การบ้าน")

# ส่วนอัปโหลดไฟล์
st.subheader("Upload CSV for Analysis")
uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
if uploaded_file is not None:
    try:
        st.session_state.uploaded_data = pd.read_csv(uploaded_file)
        st.success("File successfully uploaded and read.")
        st.write("### Uploaded Data Preview")
        st.dataframe(st.session_state.uploaded_data.head())
    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")

# Checkbox สำหรับเปิด/ปิดการวิเคราะห์ข้อมูล
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# เซต Session state สำหรับ history ถ้ายังไม่มี
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# กลับมาแสดงประวัติข้อความ
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

# รับข้อความจากผู้ใช้
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    try:
        if "uploaded_data" in st.session_state:
            df = st.session_state.uploaded_data

            if analyze_data_checkbox and ("analyze" in user_input.lower() or "insight" in user_input.lower()):
                data_description = df.describe().to_string()
                prompt = f"Analyze the following dataset and provide insights:\n\n{data_description}"
                response = model.generate_content(prompt)
                bot_response = response.text
            else:
                response = model.generate_content(user_input)
                bot_response = response.text
        else:
            if analyze_data_checkbox:
                bot_response = "Please upload a CSV file first, then ask me to analyze it."
            else:
                bot_response = model.generate_content(user_input).text

        st.session_state.chat_history.append(("assistant", bot_response))
        st.chat_message("assistant").markdown(bot_response)

    except Exception as e:
        st.error(f"An error occurred while generating the response: {e}")
