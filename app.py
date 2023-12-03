import datetime
from flask import Flask, render_template, jsonify, request
from controllers.AppOrchestrator import AppOrchestrator
import os
import openai

app = Flask(__name__)

# Initialize AppOrchestrator
orchestrator = AppOrchestrator()


# @app.route('/')
# def index_call():
#     return render_template('graph.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    eula_o_k = os.environ.get('EULA_O_K')
    openai_api_key = os.environ.get('OPENAI_API_KEY')

    if request.method == 'POST':
        if 'agree' in request.form:
            eula_o_k = 'TRUE'
            openai_api_key = request.form.get('openai_api_key')
            if openai_api_key:
                os.environ['OPENAI_API_KEY'] = openai_api_key
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
        openai.api_key = os.getenv('OPENAI_API_KEY')
        models = openai.Model.list()
        model_options = [{'label': model['id'], 'value': model['id']} for model in models['data'] if 'annalect' not in model['id']]
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
        return jsonify(updated_graph)
    except Exception as e:
        orchestrator.logger.error(f"Error in matrix sudoku approach: {e}")
        return jsonify({"status": "error", "message": str(e)})


@app.route('/impressum', methods=['GET', 'POST'])
def impressum():
    return render_template('impressum.html')


if __name__ == '__main__':
    app.run(debug=True)
