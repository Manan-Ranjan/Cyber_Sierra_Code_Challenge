# Chatbot with CSV/XLS Document Analysis

## Project Overview

A Streamlit-based AI chatbot that lets users upload CSV and Excel files and interact with their datasets using natural language. The application uses LangChain and OpenAI's GPT-4o-mini model to provide intelligent, context-aware responses while maintaining conversational history.

---

## Key Features

- Upload and analyse multiple CSV and Excel files simultaneously (CSV, XLSX, XLS)
- Converts uploaded files into Pandas DataFrames for processing
- Generates dataset quality reports including:
  - Row and column counts
  - Missing values and duplicate records
  - Numeric and categorical column detection
- Answers questions about uploaded datasets using AI; falls back to general model knowledge otherwise
- Maintains conversation history across interactions
- Supports real-time streaming of AI responses
- Create, reuse, and delete saved prompts (persisted in JSON)
- Like/dislike feedback functionality for AI responses
- Clear chat history or remove uploaded documents without restarting

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core language |
| Streamlit | Web UI framework |
| Pandas | Data processing |
| LangChain | LLM orchestration |
| LangChain OpenAI | OpenAI integration |
| OpenAI GPT-4o-mini | Language model |
| Python-dotenv | Environment variable management |

---

## Project Structure

```
project/
│
├── Code_Challenge_Chatbot.py
├── saved_prompts.json
├── feedback_log.csv
├── .env
├── requirements.txt
└── README.md
```

---

## Installation

Install all required dependencies:

```bash
pip install -r requirements.txt
```

**`requirements.txt`**

```
streamlit
pandas
python-dotenv
langchain
langchain-openai
langchain-core
openpyxl
xlrd
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
openAIkey=your_api_key_here
```

The application loads it at startup:

```python
load_dotenv()
```

---

## Application Workflow

### 1. Load Environment Variables

The API key is loaded from `.env` for secure access without hardcoding credentials.

### 2. Initialize Streamlit Application

```python
st.set_page_config(page_title="Chatbot")
st.title("Chatbot")
```

Provides a main chat interface, sidebar controls, file upload, dataset preview, and saved prompt management.

### 3. Initialize Language Model

```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("openAIkey"),
    streaming=True
)
```

Streaming is enabled so responses appear incrementally as they are generated.

### 4. Session State Management

Streamlit reruns on every interaction; session state preserves:

- Chat history
- Uploaded files
- Document processing status
- Saved prompts and selected prompt
- Feedback tracking

### 5. Upload Documents

Users upload files through the sidebar (CSV, XLSX, XLS). Files are converted to Pandas DataFrames:

```python
df = pd.read_csv(file)
# or
df = pd.read_excel(file)
```

Processed files are stored in `st.session_state.files`.

### 6. Data Processing and Quality Report

Clicking **Process Documents** triggers:

- File validation and empty dataset checking
- Numeric column conversion
- Missing value and duplicate detection
- Column type identification

**Sample quality report output:**

```
Rows: 500
Columns: 8
Missing Values: 12
Duplicates: 5
```

### 7. Preview Uploaded Data

Users select a file, choose a row count, and view the dataset in an interactive table:

```python
st.dataframe(selected_dataframe.head(rows))
```

### 8. Document Context for the LLM

The chatbot builds a context summary from each uploaded file:

```
FILE NAME: Sales.csv

COLUMNS: ['Product', 'Price', 'Quantity']

TOTAL ROWS: 500

SAMPLE DATA:
Product  Price  Quantity
Laptop   900    5
Phone    500    10
```

### 9. Saved Prompts

Commonly used queries (e.g. *"Summarize this dataset"*, *"Find missing values"*) can be saved to `saved_prompts.json` and reused or deleted from the sidebar.

### 10. Chat Interface

```python
st.chat_input()
```

Accepts normal questions, saved prompt execution, and follow-up questions.

### 11. Conversation History

Messages use LangChain's `HumanMessage` / `AIMessage` objects. The last 20 messages are included per request:

```python
st.session_state.chat[-20:]
```

### 12. System Prompt

The system prompt instructs the model to:

- Answer using uploaded dataset context
- Avoid hallucinating information not present in the data
- Use general knowledge when the question is unrelated to the data
- Maintain conversational continuity

### 13. Generate AI Response

The application sends system instructions, conversation history, document context, and the user question. Responses stream in real time:

```python
for chunk in llm.stream(messages):
    ...
```

### 14. Feedback System

Users rate each AI response with 👍 or 👎. Feedback is appended to `feedback_log.csv`:

```
timestamp,message_index,question,answer,rating
2026-08-06,2,Total sales?,Sales are...,positive
```

---

## User Interface

### Main Page
- Chat messages
- User input
- AI responses with inline feedback buttons

### Sidebar
- Upload and process documents
- Dataset quality report
- File preview with configurable row count
- Saved prompt creation, selection, and deletion
- Clear chat history / clear uploaded files

---

## Example Usage

1. **Upload** `Sales.xlsx` via the sidebar
2. Click **Process Document** — the app generates a quality report
3. **Ask** *"Which product generated the highest revenue?"*
4. The chatbot analyses the dataset and streams a response

---

## Data Structure Choices

| Data | Structure | Reason |
|---|---|---|
| Chat history | `list` | Ordered; messages appended chronologically |
| Uploaded files | `dict` | Keyed by filename for O(1) lookup |
| Processing status | `bool` | Binary state — processed or not |
| Saved prompts | `list` | Sequential collection, appended in creation order |
| Pending prompt | `str` / `None` | Temporary single value until dispatched |

---

## Advantages

- Simple, user-friendly interface
- Supports multiple simultaneous datasets
- Real-time AI response streaming
- Persistent conversation memory
- Built-in dataset quality analysis
- Reusable prompt library
- Feedback logging for evaluation
- Modular and easy to extend

## Limitations

- Supports only CSV and Excel formats
- Large datasets may slow processing
- Chatbot is limited to context extracted from uploaded files
- Requires a valid OpenAI API key
- Complex analytical operations may need additional tooling

---

## Future Improvements

- [ ] PDF and Word document support
- [ ] Vector database integration for semantic search
- [ ] User authentication and accounts
- [ ] Downloadable chat history
- [ ] Automatic chart and visualization generation
- [ ] Advanced statistical analysis
- [ ] Chunked retrieval for large datasets
- [ ] Database storage instead of local JSON/CSV files
- [ ] User-specific prompt libraries

---

## Conclusion

This project demonstrates how Streamlit, LangChain, Pandas, and OpenAI GPT can be combined into an intelligent document analysis chatbot. Users can upload structured datasets, query them in natural language, receive streamed AI insights, maintain multi-turn conversations, reuse saved prompts, and rate responses — forming a solid foundation for more advanced AI-powered data analysis applications.

