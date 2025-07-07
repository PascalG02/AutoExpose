import pyodbc
import ollama


# Connect and fetch query results
def fetch_data(query):
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=LAPTOP-H6CGEPKT;"
        "DATABASE=TimesheetDB;"
        "Trusted_Connection=yes;"
    )
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No results found."

    table_data = "\n".join([", ".join(str(val) for val in row) for row in rows])
    return f"Columns: {columns}\nData:\n{table_data}"

# Get response from local Gemma model
def get_llm_response(prompt, model='gemma3:1b'):
    response = ollama.chat(model=model, messages=[
        {"role": "user", "content": prompt}
    ])
    return response['message']['content'].strip()

# Generate SQL query from natural question
def generate_sql_from_question(question):
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
    examples = """
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
    prompt = f"""
You are a SQL expert working with sql server on SSMS. Based on the schema(only use those columns provided) and examples below, generate a raw SQL query only. Do not include explanations, backticks, or labels — just the query.You MUST use SQL Server Syntax.

Schema:
{schema}

Example:
{examples}

Question: {question}
"""
    # Get response from the LLM
    response = get_llm_response(prompt)

    # Remove any wrapping like ```sql or ```
    clean_query = response.strip()
    if clean_query.startswith("```sql"):
        clean_query = clean_query.removeprefix("```sql").strip()
    if clean_query.endswith("```"):
        clean_query = clean_query.removesuffix("```").strip()

    return clean_query

# Generate a friendly summary of the result
def generate_friendly_answer(question, sql_query, query_result):
    prompt = f"""
You are a helpful assistant. A user asked:

"{question}"

You generated this SQL:
{sql_query}

It returned this data:
{query_result}

Provide a friendly, conversational explanation of the result in a short paragraph which answers the user's question directly.
"""
    return get_llm_response(prompt)

# Run the full workflow
if __name__ == "__main__":

    print("Hi! I'm your AI assistant for Timesheet queries. Let's get started!")
    question = input("💬 How can I be of assistance: ")
    
    print("🧠 Interpreting question...")
    sql_query = generate_sql_from_question(question)
    print("📝 Generated SQL:\n", sql_query)

    print("\n🔎 Executing SQL...")
    result = fetch_data(sql_query)
    print("\n📊 Query Result:\n", result)

    print("\n💬 Friendly Answer:")
    friendly = generate_friendly_answer(question, sql_query, result)
    print(friendly)

