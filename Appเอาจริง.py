import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# ==============================
# Page Configuration
# ==============================
st.set_page_config(page_title="Gemini AI Python Code Generator for DataFrame", layout="wide")
st.title("น้องแชตบอทรายงานยอดขาย")
st.markdown("AI will generate Python code to answer your DataFrame questions!")

# ==============================
# Gemini API Key: ใส่ตรงนี้
# ==============================
try:
    genai.configure(api_key="AIzaSyDhcBaFpk3YqRJtb6kLfQhbJSnGoklha8o")
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    st.success("Gemini API Key successfully configured!")
except Exception as e:
    st.error(f"Error setting up the Gemini model: {e}")
    st.stop()

# ==============================
# Session State Initialization
# ==============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploaded_data" not in st.session_state:
    st.session_state.uploaded_data = None

# ==============================
# Load Data From Local Files
# ==============================
try:
    data_file = "transactions.csv"
    data_dict_file = "data_dict.csv"

    df_data = pd.read_csv(data_file)
    df_dict = pd.read_csv(data_dict_file)

    st.session_state.uploaded_data = df_data

    st.success(f"Successfully loaded '{data_file}' and '{data_dict_file}'")
    st.write("###  Data Preview")
    st.dataframe(df_data.head())

    st.write("### 📖 Data Dictionary")
    st.dataframe(df_dict.head())

except Exception as e:
    st.error(f"Error loading data files: {e}")
    df_data = None
    df_dict = None

# ==============================
# Display Chat History
# ==============================
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# ==============================
# Chat Input
# ==============================
if user_input := st.chat_input("Type your data question here..."):

    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    if model:
        try:
            if st.session_state.uploaded_data is not None:
                df_name = "df_data"
                data_dict_text = df_dict.to_string()
                example_record = df_data.head(2).to_string()

                prompt = f"""
                You are a helpful Python code generator.
                Your goal is to write Python code snippets based on the user's question
                and the provided DataFrame information.

                Here's the context:
                **User Question:**
                {user_input}

                **Main DataFrame (df_data):**
                {df_name}

                **Data Dictionary:**
                {data_dict_text}

                **Sample Data (Top 2 Rows):**
                {example_record}

                **Instructions:**
                - Use `exec()` and store result in `ANSWER`
                - Don't import pandas
                - Use datetime if needed
                """

                response = model.generate_content([prompt, user_input])
                generated_code = response.text

                if "```python" in generated_code:
                    code_block = generated_code.split("```python")[1].split("```")[0].strip()
                else:
                    code_block = generated_code.strip()

                try:
                    local_vars = {"df_data": df_data, "df_dict": df_dict, "ANSWER": None, "datetime": datetime}
                    exec(code_block, globals(), local_vars)
                    result = local_vars.get("ANSWER", "No result was stored in the ANSWER variable.")

                    is_thai = any('\u0E00' <= c <= '\u0E7F' for c in user_input)

                    explain_prompt = f"""
                    The user asked: {user_input}
                    Here is the result: {str(result)}
                    {'Respond in Thai language.' if is_thai else 'Respond in English.'}
                    """

                    explanation_response = model.generate_content(explain_prompt)
                    explanation_text = explanation_response.text

                    with st.chat_message("assistant"):
                        if isinstance(result, pd.DataFrame):
                            st.dataframe(result)
                        elif hasattr(result, '__iter__') and not isinstance(result, str):
                            st.write(result)
                        else:
                            st.write(result)

                        st.markdown(explanation_text)
                        st.session_state.chat_history.append(("assistant", explanation_text))

                except Exception as code_exec_error:
                    error_message = f"Error executing generated code: {str(code_exec_error)}"
                    st.error(error_message)
                    st.session_state.chat_history.append(("assistant", f"Error: {error_message}"))
            else:
                st.error("Please make sure data is properly loaded.")
                st.session_state.chat_history.append(("assistant", "Data not loaded."))
        except Exception as e:
            st.error(f"Error processing request: {str(e)}")
            st.session_state.chat_history.append(("assistant", f"Error: {str(e)}"))
