import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, jsonify, request
import openai
import functions_framework

# Initialize Firebase Admin SDK
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': 'graph-to-agent',
})

# Import controllers
from controllers.FirestoreHandler import FirestoreHandler
from controllers.AppOrchestrator import AppOrchestrator
from controllers.CloudRunSpecificInMemoryOpenAiKeyHandling import CloudRunSpecificInMemoryOpenAiKeyHandling

# Initialize Flask app
app = Flask(__name__)

# Initialize handlers
cloud_run_spec = CloudRunSpecificInMemoryOpenAiKeyHandling()
orchestrator = AppOrchestrator()

@app.route('/', methods=['GET', 'POST'])
def index():
    eula_o_k = os.environ.get('EULA_O_K')
    openai_api_key = os.environ.get('OPENAI_API_KEY')

    if request.method == 'POST':
        if 'agree' in request.form:
            eula_o_k = 'TRUE'
            openai_api_key = request.form.get('openai_api_key')
            if openai_api_key:
                cloud_run_spec.save_api_key(openai_api_key)
                os.environ['EULA_O_K'] = eula_o_k
                return render_template('graph.html')
            else:
                return render_template('eula_agreement.html', error="Please enter the OpenAI API key.")
        else:
            return render_template('disagreement_page.html')

    if eula_o_k != 'TRUE' or not openai_api_key:
        return render_template('eula_agreement.html')
    else:
        return render_template('graph.html')


@app.route('/get-openai-models', methods=['GET'])
def get_openai_models():
    try:
        openai.api_key = cloud_run_spec.get_api_key()
        models = openai.Model.list()
        model_options = [{'label': model['id'], 'value': model['id']} for model in models['data']]
        return jsonify(model_options)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


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
        random_answer = orchestrator.select_random_answer_nodes(graph_data)  # Get the random answer
        return jsonify({"updated_graph": updated_graph, "saved_name": random_answer})  # Include it in the response
    except Exception as e:
        orchestrator.logger.error(f"Error in matrix sudoku approach: {e}")
        return jsonify({"status": "error", "message": str(e)})


@app.route('/get-json-files', methods=['GET'])
def get_json_files():
    json_dir = 'json_blueprints'  # Directory where JSON files are stored
    try:
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        return jsonify(json_files)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/load-json-file', methods=['POST'])
def load_json_file():
    data = request.json
    filename = data.get('filename')
    json_dir = 'json_blueprints'  # Directory where JSON files are stored
    try:
        with open(os.path.join(json_dir, filename), 'r') as file:
            graph_data = json.load(file)
            return jsonify(graph_data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/impressum', methods=['GET', 'POST'])
def impressum():
    return render_template('impressum.html')


# Cloud Function entry point
@functions_framework.http
def app_function(request):
    return app(request.environ, lambda x, y: y)


# For local development
if __name__ == '__main__':
    app.run(debug=True)