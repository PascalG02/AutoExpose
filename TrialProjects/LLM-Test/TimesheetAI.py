import pyodbc
import ollama
import os
from dotenv import load_dotenv
import logging

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
        self.schema = """
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
        self.examples = """
Q: What day did John take leave and what time?
A:
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

    def fetch_data(self, query):
        """Execute SQL query and return formatted results."""
        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.db_server};"
                f"DATABASE={self.db_name};"
                f"Trusted_Connection={self.db_trusted_connection};"
            )
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                if not rows:
                    return "No results found."
                table_data = "\n".join([", ".join(str(val) for val in row) for row in rows])
                return f"Columns: {columns}\nData:\n{table_data}"
        except pyodbc.Error as e:
            logger.error(f"Database error: {str(e)}")
            raise Exception(f"Failed to execute query: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    def get_llm_response(self, prompt):
        """Get response from LLM."""
        try:
            response = ollama.chat(model=self.llm_model, messages=[{"role": "user", "content": prompt}])
            return response['message']['content'].strip()
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            raise Exception(f"Failed to get LLM response: {str(e)}")

    def generate_sql_from_question(self, question):
        """Generate SQL query from natural language question."""
        if not question or not isinstance(question, str):
            raise ValueError("Question must be a non-empty string")
        
        prompt = f"""
You are a SQL expert working with SQL Server on SSMS. Based on the schema (only use those columns provided) and examples below, generate a raw SQL query only. Do not include explanations, backticks, or labels — just the query. Use SQL Server syntax.

Schema:
{self.schema}

Example:
{self.examples}

Question: {question}
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
You are a helpful assistant. A user asked: "{question}"
You generated this SQL: {sql_query}
It returned this data: {query_result}
Provide a friendly, conversational explanation of the result in a short paragraph which answers the user's question directly.
"""
        return self.get_llm_response(prompt)

    def process_query(self, question):
        """Main method to process a user query and return results."""
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