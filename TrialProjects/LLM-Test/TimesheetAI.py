import pyodbc
import ollama
import streamlit as st

# Validate SQL query
def is_valid_sql(query):
    valid_tables = ["dbo.Employee", "dbo.Timesheet"]
    query = query.lower()
    # Check if query is a SELECT statement and references valid tables
    if not query.strip().startswith("select"):
        return False
    if not any(table.lower() in query for table in valid_tables):
        return False
    # Avoid destructive queries
    if any(keyword in query for keyword in ["delete", "update", "insert", "drop"]):
        return False
    return True

# Connect and fetch query results
def fetch_data(query):
    try:
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
    except pyodbc.Error as e:
        return f"Error executing query: {str(e)}"

# Get response from local Gemma model
def get_llm_response(prompt, model='gemma:2b'):
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

Q: What project was Sarah working on last week?
A:
SELECT DISTINCT t.ClientProjectName
FROM dbo.Timesheet t
JOIN dbo.Employee e ON t.EmployeeID = e.EmployeeID
WHERE e.EmployeeName = 'Sarah'

Q: How many hours did Mike work on 2025-06-01?
A:
SELECT t.TotalHours
FROM dbo.Timesheet t
JOIN dbo.Employee e ON t.EmployeeID = e.EmployeeID
WHERE e.EmployeeName = 'Mike'
AND t.Date = '2025-06-01';
"""
    prompt = f"""
You are a SQL expert. Based on the schema and examples below, generate a raw SQL query only. Do not include explanations, backticks, or labels — just the query. Use SELECT statements only, avoid subqueries unless necessary, and ensure the query is valid for the given schema. If no employee name is provided or the question is unclear, return 'ERROR: Please specify an employee name.'

Schema:
{schema}

Examples:
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

Provide a friendly, conversational explanation of the result in a short paragraph. Use a warm, engaging tone, avoid technical jargon, and make it easy to understand. If the result is an error or "No results found," explain that clearly and suggest what the user might do next (e.g., check the employee name or rephrase the question).
"""
    return get_llm_response(prompt)

# Streamlit UI
def main():
    st.set_page_config(page_title="Timesheet AI Assistant", page_icon="📅")
    st.title("📅 Timesheet AI Assistant")
    st.write("Ask about timesheets in plain English, and I'll find the answers for you!")

    # Input form
    with st.form(key="query_form"):
        question = st.text_input("💬 How can I assist you today?", placeholder="E.g., What day did John take leave?")
        submit_button = st.form_submit_button("Submit")

    if submit_button and question:
        with st.spinner("🧠 Interpreting your question..."):
            sql_query = generate_sql_from_question(question)

        if not is_valid_sql(sql_query):
            st.error("❌ Oops! The generated query isn't valid. Please rephrase your question and try again.")
        else:
            #st.subheader("📝 Generated SQL Query")
            #st.code(sql_query, language="sql")

            with st.spinner("🔎 Fetching data from the database..."):
                result = fetch_data(sql_query)
            #st.subheader("📊 Query Result")
            #st.text(result)

            with st.spinner("💬 Crafting a friendly answer..."):
                friendly = generate_friendly_answer(question, sql_query, result)
            st.subheader("😊 Your Answer")
            st.write(friendly)

if __name__ == "__main__":
    main()