import os
import logging
import ollama
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TimesheetService:
    def __init__(self):
        self.db_server = os.getenv('DB_SERVER')
        self.db_name = os.getenv('DB_NAME')
        self.db_trusted_connection = os.getenv('DB_TRUSTED_CONNECTION', 'yes')
        self.llm_model = os.getenv('LLM_MODEL', 'gemma3:1b')
        # SQLAlchemy engine
        if self.db_trusted_connection.lower() == 'yes':
            conn_str = (
                f"mssql+pyodbc://{self.db_server}/{self.db_name}"
                f"?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
            )
        else:
            self.db_user = os.getenv('DB_USER')
            self.db_password = os.getenv('DB_PASSWORD')
            conn_str = (
                f"mssql+pyodbc://{self.db_user}:{self.db_password}@{self.db_server}/{self.db_name}"
                f"?driver=ODBC+Driver+17+for+SQL+Server"
            )
        self.engine = create_engine(conn_str, pool_pre_ping=True, pool_size=5, max_overflow=10)
        # Initialize embeddings and FAISS
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Initialize FAISS vector store with RAG context."""
        schema = """
Table: dbo.Employee
Columns:
- EmployeeID (PK, int)
- EmployeeName (nvarchar)

Table: dbo.Timesheet
Columns:
- TimesheetID (PK, int)
- EmployeeID (FK, int)
- Date (date)
- DayOfWeek (nvarchar)
- ClientID (FK, int)
- ClientProjectName (nvarchar)
- Description (nvarchar)
- Billable (nvarchar)
- Comments (nvarchar)
- TotalHours (decimal)
- StartTime (time)
- EndTime (time)
"""
        examples = [
            {
                "question": "What day did John take leave and what time?",
                "sql": """
SELECT t.Date, t.StartTime, t.EndTime, t.Comments
FROM dbo.Timesheet t
JOIN dbo.Employee e ON t.EmployeeID = e.EmployeeID
WHERE e.EmployeeName = 'John'
AND (
  t.Description LIKE '%leave%'
  OR t.Comments LIKE '%leave%'
  OR t.TotalHours = 0
  OR t.StartTime IS NULL
);
"""
            },
            {
                "question": "How long did Pascal work on TaskA?",
                "sql": """
SELECT SUM(t.TotalHours)
FROM dbo.Timesheet t
JOIN dbo.Employee e ON t.EmployeeID = e.EmployeeID
WHERE e.EmployeeName = 'Pascal'
AND t.Description = 'TaskA';
"""
            },
            {
                "question": "Who didn't submit May timesheet?",
                "sql": """
SELECT e.EmployeeName
FROM dbo.Employee e
WHERE NOT EXISTS (
  SELECT 1
  FROM dbo.Timesheet t
  WHERE t.EmployeeID = e.EmployeeID
  AND t.Date LIKE '2025-05%'
);
"""
            },
            {
                "question": "What days did teamA work on ProjectA?",
                "sql": """
SELECT t.Date, t.DayOfWeek
FROM dbo.Timesheet t
JOIN dbo.Employee e ON t.EmployeeID = e.EmployeeID
WHERE t.ClientProjectName = 'ProjectA'
AND e.EmployeeName IN (SELECT EmployeeName FROM dbo.Employee WHERE Team = 'teamA');
"""
            },
            {
                "question": "What was the latest timesheet entry month?",
                "sql": """
SELECT FORMAT(MAX(t.Date), 'yyyy-MM')
FROM dbo.Timesheet t;
"""
            }
        ]
        # Combine schema and examples into context documents
        context_docs = [schema] + [f"Q: {ex['question']}\nA: {ex['sql']}" for ex in examples]
        # Create FAISS vector store
        self.vector_store = FAISS.from_texts(context_docs, self.embeddings)

    def fetch_data(self, query):
        """Execute SQL query and return formatted results using SQLAlchemy."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                columns = result.keys()
                rows = result.fetchall()
                if not rows:
                    return "No results found."
                table_data = "\n".join([str(row) for row in rows])
                return f"Columns: {columns}\nData:\n{table_data}"
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            raise Exception(f"Failed to execute query: {str(e)}")

    def get_llm_response(self, prompt):
        """Get response from Ollama LLM."""
        try:
            response = ollama.chat(model=self.llm_model, messages=[{"role": "user", "content": prompt}])
            return response['message']['content'].strip()
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            raise Exception(f"Failed to get LLM response: {str(e)}. Ensure Ollama is running and the model 'gemma3:1b' is pulled.")

    def generate_sql_from_question(self, question):
        """Generate SQL query from natural language question using FAISS RAG."""
        if not question or not isinstance(question, str):
            raise ValueError("Question must be a non-empty string")
        
        # Retrieve relevant context from FAISS
        matched_docs = self.vector_store.similarity_search(question, k=3)
        context = "\n\n".join([doc.page_content for doc in matched_docs])
        
        prompt = f"""
You are a SQL expert working with SQL Server on SSMS. Based on the schema and examples below, generate a raw SQL query only. Do not include explanations, backticks, or labels — just the query. Use SQL Server syntax.

Context:
{context}

Query: {question}
"""
        clean_query = self.get_llm_response(prompt).strip()
        for prefix in ["```sql", "```"]:
            clean_query = clean_query.removeprefix(prefix).strip()
        for suffix in ["```"]:
            clean_query = clean_query.removesuffix(suffix).strip()
        return clean_query

    def generate_friendly_answer(self, question, sql_query, query_result):
        """Generate a conversational response from query results."""
        prompt = f"""
You are a friendly assistant. A user asked: "{question}"
You ran this SQL query: {sql_query}
It returned: {query_result}
Answer the question in a conversational, friendly tone using only the data provided. Avoid technical jargon or mentioning SQL.
"""
        return self.get_llm_response(prompt)

    def process_query(self, question):
        """Process a user query and return results."""
        try:
            logger.info(f"Processing question: {question}")
            sql_query = self.generate_sql_from_question(question)
            logger.info(f"Generated SQL: {sql_query}")
            result = self.fetch_data(sql_query)
            logger.info(f"Query Result: {result}")
            friendly = self.generate_friendly_answer(question, sql_query, result)
            logger.info(f"Friendly Answer: {friendly}")
            return {
                "question": question,
                "sql_query": sql_query,
                "data": result,
                "answer": friendly
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise