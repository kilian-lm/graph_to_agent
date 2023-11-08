from flask import Flask, render_template, request, jsonify, session
import os
import json
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
import logging
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account



import datetime
import json

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from google.cloud.exceptions import NotFound

from flask import Flask, render_template
import json

from flask import Flask, render_template, jsonify, request
import json
from controllers.BigQueryHandler import BigQueryHandler
from controllers.GptAgentInteractions import GptAgentInteractions

app = Flask(__name__)

# Initialize BigQueryHandler
# bq_handler = BigQueryHandler('graph_to_agent')
gpt_agent_interactions = GptAgentInteractions('graph_to_agent')

logging.basicConfig(level=logging.DEBUG)  # You can change the level as needed.
logger = logging.getLogger(__name__)


class App:
    def __init__(self):
        self.app = Flask(__name__)
        # self.gpt_agent_interactions = BigQueryHandler('graph_to_agent')
        self.gpt_agent_interactions = GptAgentInteractions('graph_to_agent')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.setup_routes()

    def index_call(self):
        return render_template('graph.html')

    def get_graph_data(self):
        try:
            graph_id = request.json['graph_id']
            graph_data = self.gpt_agent_interactions.load_graph_data_by_id(graph_id)
            return jsonify(graph_data)
        except Exception as e:
            self.logger.error(f"Error fetching graph data: {e}")
            return jsonify({"status": "error", "message": str(e)})

    def get_available_graphs(self):
        try:
            available_graphs = self.gpt_agent_interactions.get_available_graphs()
            return jsonify(available_graphs)
        except Exception as e:
            self.logger.error(f"Error loading available graphs: {e}")
            return jsonify({"status": "error", "message": str(e)})

    def return_gpt_agent_answer_to_graph(self):
        try:
            graph_data = request.json
            self.logger.debug(f"return_gpt_agent_answer_to_graph, graph_data: {graph_data}")
            processed_data = self.gpt_agent_interactions.translate_graph_to_gpt_sequence(graph_data)
            self.logger.debug(f"return_gpt_agent_answer_to_graph, processed_data: {processed_data}")

            gpt_response = self.gpt_agent_interactions.extract_and_send_to_gpt(processed_data)
            self.logger.debug(f"return_gpt_agent_answer_to_graph, gpt_response: {gpt_response}")

            updated_graph = self.gpt_agent_interactions.process_gpt_response_and_update_graph(gpt_response, graph_data)
            self.logger.debug(f"return_gpt_agent_answer_to_graph, updated_graph: {updated_graph}")

            return jsonify({"status": "success", "updatedGraph": updated_graph})
        except Exception as e:
            self.logger.error(f"Error processing GPT agent request: {e}")
            return jsonify({"status": "error", "message": str(e)})

    def save_graph(self):
        try:
            graph_data = request.json
            self.logger.debug(f"save_graph, graph_data: {graph_data}")

            graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            self.logger.debug(f"save_graph, graph_id: {graph_id}")
            errors = self.gpt_agent_interactions.save_graph_data(graph_data, graph_id)

            self.logger.error(f"save_graph, errors: {errors}")

            if errors:
                return jsonify({"status": "error", "message": "Failed to save some data.", "errors": errors})

            return jsonify({"status": "success", "message": "Graph saved successfully!"})
        except Exception as e:
            self.logger.error(f"Error saving graph: {e}")
            return jsonify({"status": "error", "message": str(e)})

    def setup_routes(self):
        self.app.route('/')(self.index_call)
        self.app.route('/get-graph-data', methods=['POST'])(self.get_graph_data)
        self.app.route('/get-available-graphs', methods=['GET'])(self.get_available_graphs)
        self.app.route('/return-gpt-agent-answer-to-graph', methods=['POST'])(self.return_gpt_agent_answer_to_graph)
        self.app.route('/save-graph', methods=['POST'])(self.save_graph)

    def run(self):
        self.app.run(debug=True)


if __name__ == '__main__':
    server = App()
    server.run()
