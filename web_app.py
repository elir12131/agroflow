# web_app.py

from flask import Flask, render_template, request, jsonify
from database import Database
import json

# Initialize the Flask app and the database
app = Flask(__name__)
db = Database()

# --- Page Route ---
# This route serves the main HTML page to the user's browser.
@app.route('/')
def index():
    # render_template looks for files in a 'templates' folder
    return render_template('index.html')

# --- API Endpoints (The Backend's "Doors") ---
# The frontend will talk to these endpoints to get and save data.

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """API endpoint to get a list of all customers."""
    customers = db.get_customers()
    # Convert the database rows to a list of dictionaries so it can be sent as JSON
    customer_list = [dict(row) for row in customers]
    return jsonify(customer_list)

@app.route('/api/customers/add', methods=['POST'])
def add_customer():
    """API endpoint to add a new customer."""
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')

    if not name:
        return jsonify({'success': False, 'message': 'Name is required'}), 400

    db.add_customer(name, email, phone, "", "") # Address and Notes are empty for this example
    return jsonify({'success': True, 'message': 'Customer added successfully'})

if __name__ == '__main__':
    # This allows you to run the app locally for testing
    app.run(debug=True)
