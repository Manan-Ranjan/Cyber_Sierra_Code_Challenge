import os
import json
import csv
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


# Loading environment variables
load_dotenv()

# Displaying the user interface
st.set_page_config(page_title="Chatbot")
st.title("Chatbot")

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("openAIkey"),
    streaming=True,
)

# Files used for permanent storage
PROMPTS_FILE="saved_prompts.json"
FEEDBACK_FILE="feedback_log.csv"


# File handling for saved prompts 
def load_saved_prompts():
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, "r", encoding="utf-8") as promptfile:
            return json.load(promptfile)

    return []


def save_prompts(prompts):
    with open(PROMPTS_FILE, "w", encoding="utf-8") as promptfile:
        json.dump(prompts,promptfile)


# Feedback File handling 
def log_feedback(message_index, question, answer, rating):
    file_exists = os.path.exists(FEEDBACK_FILE)

    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as feedbackfile:
        writer = csv.writer(feedbackfile)

        if not file_exists:
            writer.writerow(["timestamp","message_index","question","answer","rating"])

        writer.writerow([datetime.now().isoformat(),message_index,question,answer,rating])

def feedback_buttons(message_index, question, answer):
    col1, col2 = st.columns(2)
    like_key = f"like_{message_index}"
    dislike_key = f"dislike_{message_index}"

    if col1.button("👍", key=like_key):
        log_feedback(message_index, question, answer, "positive")
        st.toast("Feedback saved!")

    if col2.button("👎", key=dislike_key):
        log_feedback(message_index, question, answer, "negative")
        st.toast("Feedback saved!")

# Session state
if "chat" not in st.session_state:
    st.session_state.chat = []

if "files" not in st.session_state:
    st.session_state.files = {}

if "processed" not in st.session_state:
    st.session_state.processed = False

# Saved prompts on the file so they survive restarts
if "saved_prompts" not in st.session_state:
    st.session_state.saved_prompts = load_saved_prompts()

if "pending_saved_prompt" not in st.session_state:
    st.session_state.pending_saved_prompt = None

# Tracks which assistant messages already received feedback this session
if "feedback" not in st.session_state:
    st.session_state.feedback = {}


# Function to build context from uploaded files
def create_document_context():

    if not st.session_state.files:
        return ""

    context = ""

    for name, df in st.session_state.files.items():

        context += f"""
            FILE NAME:
            {name}

            COLUMNS:
            {list(df.columns)}

            TOTAL ROWS:
            {len(df)}

            SAMPLE DATA:
            {df.head(int(os.getenv("DEFAULT_ROWS"))).to_string(index=False)}"""

    return context


# Creating a sidebar interface
with st.sidebar:

    st.header("Settings")

    # File uploader to upload files
    uploaded_files = st.file_uploader(
        "Upload Documents",
        accept_multiple_files=True,
    )

    # Processer to process uploaded files
    process = st.button("Process Documents")

    if process and uploaded_files:

        with st.spinner("Processing documents..."):

            dataframes = {}

            for file in uploaded_files:

                try:
                    # CSV file processor
                    if file.name.endswith(".csv"):
                        df=pd.read_csv(file)
                        st.write("The datatypes of the file ",df.dtypes)

                    # Excel file processor
                    elif file.name.endswith(".xlsx"):
                        df=pd.read_excel(file, engine="openpyxl")
                        st.write("The datatypes of the file ",df.dtypes)

                    elif file.name.endswith(".xls"):
                        df=pd.read_excel(file, engine="xlrd")
                        st.write("The datatypes of the file ",df.dtypes)

                    # Error warning for unsupported file format
                    else:
                        st.warning(f"Unsupported file format: {file.name}")
                        continue
                    
                    # Error warning for empty file 
                    if df.isnull().all().all():
                        st.warning(f"{file.name}: Dataset contains only missing values.")
                        continue

                    # Convert numeric-looking columns
                    for col in df.columns:
                        converted = pd.to_numeric(
                        df[col].astype(str).str.replace(r"[$,]", "", regex=True),
                        errors="coerce"
                        )

                        if converted.notna().sum() == len(df):
                            df[col] = converted
                    
                    # Data Engineering dashboard 
                    profile = {
                        "rows": len(df),
                        "columns": len(df.columns),
                        "missing_values": df.isnull().sum().sum(),
                        "duplicates": df.duplicated().sum(),
                    }

                    numeric_columns = df.select_dtypes(
                        include="number"
                        ).columns.tolist()

                    categorical_columns = df.select_dtypes(
                    include=["object", "category"]
                    ).columns.tolist()

                    duplicate_count = df.duplicated().sum()

                    dataframes[file.name] = df

                    st.subheader(f"Data Quality Report - {file.name}")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Rows", profile["rows"])
                        st.metric("Columns", profile["columns"])
                        st.metric("Missing Values", profile["missing_values"])

                    with col2:
                        st.metric("Numeric Columns", len(numeric_columns))
                        st.metric("Categorical Columns", len(categorical_columns))
                        st.metric("Duplicates", duplicate_count)

                    # Warning for missing values 
                    if profile["missing_values"] > 0:
                        st.warning(f"{file.name} contains {profile['missing_values']} null values.")
                    
                    # Warning for duplicate values
                    if duplicate_count > 0:
                        st.warning(f"{file.name} contains {duplicate_count} duplicate rows.")

                except Exception as error:
                    st.error(f"Could not process {file.name}: {error}")

            st.session_state.files = dataframes
            st.session_state.processed = True

        st.success("Documents processed successfully!")

    if st.session_state.files:
        st.divider()
        st.subheader("Preview File")

        # Dropdown with all the uploaded file names
        selected_file = st.selectbox(
            "Select file",
            list(st.session_state.files.keys()))

        # Input slider to select the number of rows to be dispayed
        rows = st.number_input(
            "Preview rows",
            min_value=int(os.getenv("MIN_ROWS")),
            max_value=int(os.getenv("MAX_ROWS")),
            value=int(os.getenv("DEFAULT_ROWS")))

        # Display of user specified rows and coloumns
        st.dataframe(
            st.session_state.files[selected_file].head(rows))

    st.divider()
    st.subheader("Saved Prompts")

    # To create reusable prompts that can be saved and used multiple times
    new_prompt = st.text_area("Create a saved prompt")

    if st.button("Save Prompt") and new_prompt.strip():
        st.session_state.saved_prompts.append(new_prompt.strip())
        save_prompts(st.session_state.saved_prompts)
        st.success("Prompt saved")
        st.rerun()
    # To send the reusable prompts straight to the chatbot
    if st.session_state.saved_prompts:

        st.caption("Click a saved prompt to send it immediately:")

        for i, saved in enumerate(st.session_state.saved_prompts):

            label = saved if len(saved) <= 40 else saved[:37] + "..."
            # option to save or delete a prompt 
            prompt_col, delete_col = st.columns([5, 1])

            with prompt_col:
                if st.button(label, key=f"saved_prompt_btn_{i}"):
                    st.session_state.pending_saved_prompt = saved
                    st.rerun()

            with delete_col:
                if st.button("✕", key=f"saved_prompt_del_{i}"):
                    st.session_state.saved_prompts.pop(i)
                    save_prompts(st.session_state.saved_prompts)
                    st.rerun()

    st.divider()
    #Option to clear chat or clear uploaded files but not saved prompts 
    clear_chat = st.button("Clear Chat")
    clear_files = st.button("Clear Uploaded Files")

# Clear functions 
if clear_chat:
    st.session_state.chat = []
    st.session_state.feedback = {}
    st.rerun()

if clear_files:
    st.session_state.files = {}
    st.session_state.processed = False
    st.rerun()


# Displaying the chat history
for idx, message in enumerate(st.session_state.chat):
    role = ("user"
        if isinstance(message, HumanMessage)
        else "assistant")

    with st.chat_message(role):
        st.write(message.content)

        if role == "assistant" and idx > 0:
            question = st.session_state.chat[idx - 1].content
            feedback_buttons(idx, question, message.content)

        


# Chat input interface
typed_prompt = st.chat_input("Ask anything")

# Using the saved prompt if selected
if st.session_state.pending_saved_prompt:
    prompt = st.session_state.pending_saved_prompt
    st.session_state.pending_saved_prompt = None
else:
    prompt = typed_prompt


# Generating the response
if prompt:
    st.session_state.chat.append(HumanMessage(content=prompt))

    with st.chat_message("user"):
        st.write(prompt)

    # Collecting the file context
    document_context = create_document_context()

    messages = [
        SystemMessage(
            content="""

You are a helpful chatbot.

Answer questions using uploaded CSV/XLS data.

If question asks for something other than what is in the data then use your own knowledge

Use the provided extracted rows to answer.

If the information is unavailable, say so.

Do not invent data.

Maintain conversational continuity.

"""
        )
    ]

    # Including the recent conversation in the chatbot's reply
    messages.extend(
        st.session_state.chat[-20:])

    # Adding the uploaded file context
    if document_context:

        messages.append(HumanMessage(
                content=f"""
                    Uploaded Document Context:
                    {document_context}

                    User Question:
                    {prompt}"""))

    # Streaming the model response
    with st.chat_message("assistant"):
        answer = ""
        response_box = st.empty()

        for chunk in llm.stream(messages):
            if chunk.content:
                answer += chunk.content
                response_box.markdown(answer)

    # Saving the chatbot reply
    st.session_state.chat.append(
        AIMessage(content=answer)
    )

    # Rerun the AI application 
    st.rerun()