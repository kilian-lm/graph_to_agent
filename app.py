import os
import datetime
from flask import Flask, render_template, jsonify, request
import json
import uuid
import logging

# All custom classes
from logger.CustomLogger import CustomLogger
from controllers.EngineRoom import EngineRoom
from controllers.v2GptAgentInteractions import v2GptAgentInteractions
from controllers.BigQueryHandler import BigQueryHandler
from controllers.v1GraphPatternProcessor import GraphPatternProcessor

app = Flask(__name__)


class App():
    def __init__(self):
        # Basics
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.general_uuid = str(uuid.uuid4())
        self.key = f"{self.timestamp}_{self.general_uuid}"
        print(self.timestamp)
        self.log_file = f'{self.timestamp}_{self.general_uuid}_app.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)

        # All custom classes
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)
        self.engine_room = EngineRoom(self.key, 'graph_to_agent')
        self.gpt_agent_interactions = v2GptAgentInteractions(self.key, 'graph_to_agent')
        self.bq_handler = BigQueryHandler(self.key,
                                          'graph_to_agent')  # Todo :: need to adapt dataset logic not for instantiating

        # All Checkpoints and Externalities
        self.logs_bucket = os.getenv('LOGS_BUCKET')  # ToDo :: If bucket doesnt exist, create
        self.edges_table = os.getenv('EDGES_TABLE')
        self.nodes_table = os.getenv('NODES_TABLE')
        self.matrix_dataset_id = os.getenv('MATRIX_DATASET_ID')
        self.graph_dataset_id = os.getenv('GRAPH_DATASET_ID')
        self.graph = None
        self.num_steps = os.getenv('NUM_STEPS')  # Todo :: implement UI element to set num_steps
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = os.getenv('OPENAI_BASE_URL')

        self.app = Flask(__name__)
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
        graph_data = request.json
        self.logger.info(f"return_gpt_agent_answer_to_graph, graph_data: {graph_data}")
        # gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data)
        updated_graph = self.engine_room.main_tree_based_design_general(graph_data)
        # print(gpt_response)
        print(updated_graph)
        # breakpoint()
        # timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        # filename = f"temp_local/debugging_var_method_{self.timestamp}.json"
        #
        # # Check if the temp_local directory exists
        # if not os.path.exists('temp_local'):
        #     os.makedirs('temp_local')
        #
        # # Save the JSON data to the file
        # with open(filename, 'w') as json_file:
        #     json_file.write(json.dumps(graph_data))  # Serialize dict to JSON formatted string
        #
        # processed_data = self.gpt_agent_interactions.translate_graph_to_gpt_sequence(graph_data)
        # self.logger.info(f"return_gpt_agent_answer_to_graph, processed_data: {processed_data}")
        #
        # # Identify if any @variable placeholders are present
        # variable_node_present = any('@variable' in node['label'] for node in graph_data['nodes'])
        # self.logger.info(f"return_gpt_agent_answer_to_graph, variable_node_present: {variable_node_present}")
        #
        # if variable_node_present:
        #     # Call the populate_variable_nodes method
        #     # Note: You need to obtain the initial GPT response to populate the base @variable
        #     initial_gpt_response = self.gpt_agent_interactions.extract_and_send_to_gpt(processed_data)
        #     self.logger.info(f"return_gpt_agent_answer_to_graph, initial_gpt_response: {initial_gpt_response}")
        #     updated_graph = self.gpt_agent_interactions.populate_variable_nodes(graph_data, initial_gpt_response)
        #     self.logger.info(f"return_gpt_agent_answer_to_graph, updated_graph: {updated_graph}")
        #
        # else:
        #     # Continue with the legacy workflow
        #     # gpt_response = self.gpt_agent_interactions.extract_and_send_to_gpt(processed_data)
        #
        #     # gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data)
        #     # gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data_json)
        #     gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data)
        #
        #     self.logger.info(f"return_gpt_agent_answer_to_graph, gpt_response: {gpt_response}")
        #     updated_graph = self.gpt_agent_interactions.process_gpt_response_and_update_graph(gpt_response, graph_data)
        #     self.logger.info(f"return_gpt_agent_answer_to_graph, updated_graph: {updated_graph}")

        return jsonify({"status": "success", "updatedGraph": updated_graph})

    # except Exception as e:
    #     self.logger.error(f"Error processing GPT agent request: {e}")
    #     return jsonify({"status": "error", "message": str(e)})

    # def return_gpt_agent_answer_to_graph(self):
    #     try:
    #         graph_data = request.json
    #         self.logger.info(f"return_gpt_agent_answer_to_graph, graph_data: {graph_data}")
    #         processed_data = self.gpt_agent_interactions.translate_graph_to_gpt_sequence(graph_data)
    #         self.logger.info(f"return_gpt_agent_answer_to_graph, processed_data: {processed_data}")
    #
    #         # todo :: check via if else for @variable node, if no var, than legacy workflow
    #         self.gpt_agent_interactions.populate_variable_nodes()
    #
    #
    #         gpt_response = self.gpt_agent_interactions.extract_and_send_to_gpt(processed_data)
    #         self.logger.info(f"return_gpt_agent_answer_to_graph, gpt_response: {gpt_response}")
    #
    #         updated_graph = self.gpt_agent_interactions.process_gpt_response_and_update_graph(gpt_response, graph_data)
    #         self.logger.info(f"return_gpt_agent_answer_to_graph, updated_graph: {updated_graph}")
    #
    #         return jsonify({"status": "success", "updatedGraph": updated_graph})
    #     except Exception as e:
    #         self.logger.error(f"Error processing GPT agent request: {e}")
    #         return jsonify({"status": "error", "message": str(e)})

    def save_graph(self):
        try:
            graph_data = request.json
            self.logger.info(f"save_graph, graph_data: {graph_data}")

            # graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            self.logger.info(f"save_graph, graph_id: {self.timestamp}")
            msg = self.gpt_agent_interactions.save_graph_data(graph_data, self.key)
            self.logger.info(msg)
            # self.logger.error(f"save_graph, errors: {errors}")
            #
            # if errors:
            #     return jsonify({"status": "error", "message": "Failed to save some data.", "errors": errors})

            return jsonify({"status": "success", "message": 200})
        except Exception as e:
            self.logger.error(f"Error saving graph: {e}")
            return jsonify({"status": "error", "message": str(e)})

    def setup_routes(self):
        self.app.route('/')(self.index_call)
        self.app.route('/get-graph-data', methods=['POST'])(self.get_graph_data)
        self.app.route('/get-available-graphs', methods=['GET'])(self.get_available_graphs)
        self.app.route('/return-gpt-agent-answer-to-graph', methods=['POST'])(self.return_gpt_agent_answer_to_graph)
        # self.app.route('/return-gpt-agent-answer-to-graph', methods=['POST'])(self.engine_room.main_tree_based_design_general)
        self.app.route('/save-graph', methods=['POST'])(self.save_graph)

    def run(self):
        self.app.run(debug=True)


if __name__ == '__main__':
    server = App()
    server.run()
