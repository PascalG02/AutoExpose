from flask import Flask,request
import TimesheetAITest as timesheet_ai

app = Flask(__name__)

@app.route('/timesheetai')
def query_ai():
    question = request.get_json()

    sql_query = timesheet_ai.generate_sql_from_question(question)
    print(f"Generated SQL Query: {sql_query}")

    result = timesheet_ai.fetch_data(sql_query)

    friendly = timesheet_ai.generate_friendly_answer(question, sql_query, result)

    print(friendly)


    return friendly