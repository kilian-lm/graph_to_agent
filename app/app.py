from flask import Flask, render_template, request, jsonify
# Include necessary imports for your Solver class
# For example:
# import requests, json, logging

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    data = request.json

    # Instantiate your Solver class and call the appropriate methods
    solver = Solver(openai_api_key="YOUR_API_KEY", url="YOUR_URL")
    problem_description = data.get("problem_description", "")
    responses = solver.model_problem_spaces(problem_description)

    # Convert responses into a format suitable for vis.js
    # This step might need additional details on how you want to visualize the results.

    return jsonify(responses)

if __name__ == "__main__":
    app.run(debug=True)
