from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from dotenv import load_dotenv
from TimesheetAI import TimesheetService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Initialize TimesheetService
timesheet_service = TimesheetService()

@app.route('/timesheetai', methods=['POST'])
def query_ai():
    try:
        # Validate JSON input
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        question = data.get('question')
        if not question or not isinstance(question, str):
            return jsonify({"error": "Invalid or missing 'question' field"}), 400

        # Process query using TimesheetService
        result = timesheet_service.process_query(question)
        
        # Return structured JSON response
        return jsonify(result), 200

    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)