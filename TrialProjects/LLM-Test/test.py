
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
def get_llm_response(prompt, model='gemma:2b'):
    response = ollama.chat(model=model, messages=[
        {"role": "user", "content": prompt}
    ])
    return response['message']['content'].strip()

# Generate SQL query from natural question
def generate_sql_from_question(question):
    schema = """
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
Q: What day did Jack take leave and what time?
A: SELECT Date, StartTime, EndTime, Comments 
   FROM dbo.Timesheet 
   WHERE EmployeeID = (SELECT EmployeeID FROM Employee WHERE EmployeeName = 'Jack') 
     AND (
       Description LIKE '%leave%' 
       OR Comments LIKE '%leave%' 
       OR TotalHours = 0 
       OR StartTime IS NULL
     );
"""
    prompt = f"""
You are a SQL expert. Based on the schema and examples below, generate a raw SQL query only. Do not include explanations, backticks, or labels — just the query.

Schema:
{schema}

Example:
{examples}

Question: {question}
"""
    # Get response
    response = get_llm_response(prompt, model='gemma:2b')

    # Remove any wrapping like ```sql or ```
    clean_query = response.strip().removeprefix("```sql").removesuffix("```").strip()
    return clean_query

# Generate a friendly summary of the result
def generate_friendly_answer(question, sql_query, query_result):
    prompt = f"""
You are a helpful assistant. A user asked the following question:

"{question}"

You generated this SQL:
{sql_query}

It returned this data:
{query_result}

Now provide a friendly, natural explanation of the result.
"""
    return get_llm_response(prompt, model='gemma:2b')

# Run the full workflow
if __name__ == "__main__":
    question = "What day did John take leave?"

    print("🧠 Interpreting question...")
    sql_query = generate_sql_from_question(question)
    print("📝 Generated SQL:\n", sql_query)

    print("\n🔎 Executing SQL...")
    result = fetch_data(sql_query)
    print("\n📊 Query Result:\n", result)

    print("\n💬 Friendly Answer:")
    friendly = generate_friendly_answer(question, sql_query, result)
    print(friendly)
