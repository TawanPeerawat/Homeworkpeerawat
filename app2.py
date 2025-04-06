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
# Gemini API Key Input
# ==============================
gemini_api_key = st.text_input("Gemini API Key:", type="password", placeholder="Enter your Gemini API Key")

# Initialize Gemini Model
model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("Gemini API Key successfully configured!")
    except Exception as e:
        st.error(f"Error setting up the Gemini model: {e}")

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
    # Read data from local files
    data_file = "transactions.csv"
    data_dict_file = "data_dict.csv"

    # Load data
    df_data = pd.read_csv(data_file)
    df_dict = pd.read_csv(data_dict_file)

    # Store in session state
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

    # Store and display user message
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process user input
    if model:
        try:
            if st.session_state.uploaded_data is not None:

                df_name = "df_data"
                data_dict_text = df_dict.to_string()
                example_record = df_data.head(2).to_string()

                # === Use your advanced prompt ===
                prompt = f"""
                You are a helpful Python code generator.
                Your goal is to write Python code snippets based on the user's question
                and the provided DataFrame information.

                Here's the context:

                **User Question:**
                {user_input}

                **Main DataFrame (df_data):**
                {df_name}

                **Data Dictionary DataFrame (df_dict):**
                This DataFrame contains explanations of columns in the main DataFrame.

                **Main DataFrame Details:**
                {data_dict_text}

                **Sample Data (Top 2 Rows of df_data):**
                {example_record}

                **Instructions:**

                1. Write Python code that addresses the user's question by querying or manipulating the DataFrame.
                2. **Crucially, use the `exec()` function to execute the generated code.**
                3. Do not import pandas
                4. Change date column type to datetime - datetime module is already imported and available
                5. **Store the result of the executed code in a variable named `ANSWER`.**
                    This variable should hold the answer to the user's question (e.g., a filtered DataFrame, a calculated value, etc.).
                6. Both DataFrames are already loaded:
                   - `df_data`: Main data DataFrame with transactions
                   - `df_dict`: Data dictionary explaining the columns in df_data
                7. Feel free to use both DataFrames to answer the question thoroughly.
                8. Keep the generated code concise and focused on answering the question.
                9. If the question requires a specific output format (e.g., a list, a single value), ensure the `ANSWER` variable holds that format.

                **Example:**
                If the user asks: "Show me the rows where the 'age' column is greater than 30."
                And the DataFrame has an 'age' column.

                The generated code should look something like this (inside the `exec()` string):

                ```python
                query_result = df_data[df_data['age'] > 30]
                ANSWER = query_result
                """

                # Generate code
                response = model.generate_content([prompt, user_input])
                generated_code = response.text
                
                # Clean and extract code
                if "```python" in generated_code:
                    code_block = generated_code.split("```python")[1].split("```")[0].strip()
                else:
                    code_block = generated_code.strip()
                
                # Execute the code
                try:
                    local_vars = {"df_data": df_data, "df_dict": df_dict, "ANSWER": None, "datetime": datetime}
                    exec(code_block, globals(), local_vars)
                    result = local_vars.get("ANSWER", "No result was stored in the ANSWER variable.")
                    
                    # Check if input is in Thai
                    is_thai = any('\u0E00' <= c <= '\u0E7F' for c in user_input)
                    
                    # Generate explanation using the model
                    explain_prompt = f"""
                    The user asked: {user_input}
                    Here is the result: {str(result)}
                    
                    Please provide a clear explanation of these results in plain language.
                    Include any relevant insights or patterns from the data.
                    Keep the explanation focused and concise.
                    {'Respond in Thai language.' if is_thai else 'Respond in English.'}
                    """
                    
                    explanation_response = model.generate_content(explain_prompt)
                    explanation_text = explanation_response.text
                    
                    # Display results
                    with st.chat_message("assistant"):
                        # Only show the explanation, not the code
                        if isinstance(result, pd.DataFrame):
                            st.dataframe(result)
                        elif hasattr(result, '__iter__') and not isinstance(result, str):
                            st.write(result)  # For lists, tuples, etc.
                        else:
                            st.write(result)  # For strings and scalar values
                            
                        st.markdown(explanation_text)
                        
                        # Store in chat history (hide code in history)
                        st.session_state.chat_history.append(("assistant", f"{explanation_text}"))
                
                except Exception as code_exec_error:
                    error_message = f"Error executing generated code: {str(code_exec_error)}"
                    st.error(error_message)
                    st.session_state.chat_history.append(("assistant", f"Error: {error_message}"))
            else:
                # Handle when data isn't loaded
                error_message = "Cannot process your request. Please make sure data is properly loaded."
                with st.chat_message("assistant"):
                    st.error(error_message)
                st.session_state.chat_history.append(("assistant", error_message))
        
        except Exception as e:
            error_message = f"Error processing your request: {str(e)}"
            with st.chat_message("assistant"):
                st.error(error_message)
            st.session_state.chat_history.append(("assistant", error_message))
    else:
        with st.chat_message("assistant"):
            st.error("Please enter a valid Gemini API Key to use this feature.")
        st.session_state.chat_history.append(("assistant", "Please enter a valid Gemini API Key to use this feature."))
