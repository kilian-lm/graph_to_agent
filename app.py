import datetime
from flask import Flask, render_template, jsonify, request
from controllers.AppOrchestrator import AppOrchestrator

app = Flask(__name__)

# Initialize AppOrchestrator
orchestrator = AppOrchestrator()

@app.route('/')
def index_call():
    return render_template('graph.html')

@app.route('/get-graph-data', methods=['POST'])
def get_graph_data():
    try:
        graph_id = request.json['graph_id']
        graph_data = orchestrator.get_graph_data(graph_id)
        return jsonify(graph_data)
    except Exception as e:
        orchestrator.logger.error(f"Error fetching graph data: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/get-available-graphs', methods=['GET'])
def get_available_graphs():
    try:
        available_graphs = orchestrator.get_available_graphs()
        return jsonify(available_graphs)
    except Exception as e:
        orchestrator.logger.error(f"Error loading available graphs: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/save-graph', methods=['POST'])
def save_graph():
    try:
        graph_data = request.json
        orchestrator.save_graph(graph_data)
        return jsonify({"status": "success", "message": 200})
    except Exception as e:
        orchestrator.logger.error(f"Error saving graph: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/return-gpt-agent-answer-to-graph', methods=['POST'])
def matrix_sudoku_approach():
    try:
        graph_data = request.json
        updated_graph = orchestrator.matrix_sudoku_approach(graph_data)
        return jsonify(updated_graph)
    except Exception as e:
        orchestrator.logger.error(f"Error in matrix sudoku approach: {e}")
        return jsonify({"status": "error", "message": str(e)})

# Add additional routes here as needed

if __name__ == '__main__':
    app.run(debug=True)
