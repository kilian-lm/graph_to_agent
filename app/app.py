from flask import Flask, render_template, request, jsonify
# Include necessary imports for your Solver class

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    data = request.json
    # Instantiate your Solver class and call the appropriate methods
    # Here, I'm just returning the data for simplicity
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
