import os
import datetime
from flask import Flask, render_template, jsonify, request
import uuid
import logging
import json

# All custom classes
from controllers.MatrixLayerOne import MatrixLayerOne
from controllers.AnswerPatternProcessor import AnswerPatternProcessor
from logger.CustomLogger import CustomLogger
from controllers.EngineRoom import EngineRoom
from controllers.GptAgentInteractions import GptAgentInteractions
from controllers.BigQueryHandler import BigQueryHandler
from controllers.GraphPatternProcessor import GraphPatternProcessor

from dotenv import load_dotenv

load_dotenv()

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
        self.engine_room = EngineRoom(self.key, os.getenv('GRAPH_DATASET_ID'))
        self.gpt_agent_interactions = GptAgentInteractions(self.key, os.getenv('GRAPH_DATASET_ID'))
        self.bq_handler = BigQueryHandler(self.key)

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

    # def return_gpt_agent_answer_to_graph(self):
    #     graph_data = request.json
    #     self.logger.info(f"return_gpt_agent_answer_to_graph, graph_data: {graph_data}")
    #     # gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data)
    #     updated_graph = self.engine_room.main_tree_based_design_general(graph_data)
    #     # print(gpt_response)
    #     print(updated_graph)
    #     # breakpoint()
    #     # timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    #     # filename = f"temp_local/debugging_var_method_{self.timestamp}.json"
    #     #
    #     # # Check if the temp_local directory exists
    #     # if not os.path.exists('temp_local'):
    #     #     os.makedirs('temp_local')
    #     #
    #     # # Save the JSON data to the file
    #     # with open(filename, 'w') as json_file:
    #     #     json_file.write(json.dumps(graph_data))  # Serialize dict to JSON formatted string
    #     #
    #     # processed_data = self.gpt_agent_interactions.translate_graph_to_gpt_sequence(graph_data)
    #     # self.logger.info(f"return_gpt_agent_answer_to_graph, processed_data: {processed_data}")
    #     #
    #     # # Identify if any @variable placeholders are present
    #     # variable_node_present = any('@variable' in node['label'] for node in graph_data['nodes'])
    #     # self.logger.info(f"return_gpt_agent_answer_to_graph, variable_node_present: {variable_node_present}")
    #     #
    #     # if variable_node_present:
    #     #     # Call the populate_variable_nodes method
    #     #     # Note: You need to obtain the initial GPT response to populate the base @variable
    #     #     initial_gpt_response = self.gpt_agent_interactions.extract_and_send_to_gpt(processed_data)
    #     #     self.logger.info(f"return_gpt_agent_answer_to_graph, initial_gpt_response: {initial_gpt_response}")
    #     #     updated_graph = self.gpt_agent_interactions.populate_variable_nodes(graph_data, initial_gpt_response)
    #     #     self.logger.info(f"return_gpt_agent_answer_to_graph, updated_graph: {updated_graph}")
    #     #
    #     # else:
    #     #     # Continue with the legacy workflow
    #     #     # gpt_response = self.gpt_agent_interactions.extract_and_send_to_gpt(processed_data)
    #     #
    #     #     # gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data)
    #     #     # gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data_json)
    #     #     gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data)
    #     #
    #     #     self.logger.info(f"return_gpt_agent_answer_to_graph, gpt_response: {gpt_response}")
    #         updated_graph = self.gpt_agent_interactions.process_gpt_response_and_update_graph(gpt_response, graph_data)
    #     self.logger.info(f"return_gpt_agent_answer_to_graph, updated_graph: {updated_graph}")
    #
    #     return jsonify({"status": "success", "updatedGraph": updated_graph})

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

    def matrix_sudoku_approach(self):
        # import json

        # timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        # general_uuid = str(uuid.uuid4())
        # key = f"{timestamp}_{general_uuid}"
        #
        # json_file_path = "./logics/simple_va_inheritance_20231117.json"
        #
        # with open(json_file_path, 'r') as json_file:
        #     graph_data = json.load(json_file)

        graph_data = request.json
        self.logger.info(f"save_graph, graph_data: {graph_data}")

        key = self.key

        gpt_agent_interactions = GptAgentInteractions(key, os.getenv('GRAPH_DATASET_ID'))

        gpt_agent_interactions.save_graph_data(graph_data, key)

        matrix_layer_one = MatrixLayerOne(key, graph_data, os.getenv('MULTI_LAYERED_MATRIX_DATASET_ID'))

        filename = matrix_layer_one.create_advanced_adjacency_matrix()
        filename

        matrix_layer_one.multi_layered_matrix_upload_jsonl_to_bigquery(filename,
                                                                       os.getenv('MULTI_LAYERED_MATRIX_DATASET_ID'))

        matrix_layer_one.adjacency_matrix_upload_to_bigquery(os.getenv('ADJACENCY_MATRIX_DATASET_ID'))

        graph_processor = GraphPatternProcessor(10, key)
        graph_processor.save_gpt_calls_to_jsonl(key)

        graph_processor.dump_to_bigquery(key, os.getenv('CURATED_CHAT_COMPLETIONS'))

        answer_pat_pro = AnswerPatternProcessor(key)
        answer_pat_pro.dump_gpt_jsonl_to_bigquery(key)
        answer_pat_pro.run()

        graph_data = self.return_gpt_agent_answer_to_graph(graph_data)

        return graph_data

    # def return_gpt_agent_answer_to_graph(self, graph_data):
    #     # SQL query to fetch distinct answer_node.node_id and answer_node.label
    #
    #     node_answers_tbl_id = f"{self.bq_handler.bigquery_client.project}.{os.getenv('ANSWER_CURATED_CHAT_COMPLETIONS')}.{self.key}"
    #     self.logger.info(f"return_gpt_agent_answer_to_graph, node_answers_tbl_id: {node_answers_tbl_id}")
    #
    #     node_answers_tbl_id = f"{self.bq_handler.bigquery_client.project}.{os.getenv('ANSWER_CURATED_CHAT_COMPLETIONS')}.20231126125746_3f77f8f3-fd76-48d1-b28c-03054e6c3a06"
    #     query = f"""
    #     SELECT DISTINCT answer_node.node_id, answer_node.label
    #     FROM `{node_answers_tbl_id}`
    #     """
    #
    #     # Execute the query
    #     query_job = self.bq_handler.bigquery_client.query(query)
    #     results = query_job.result()
    #     self.logger.info(f"return_gpt_agent_answer_to_graph, results: {results}")
    #
    #     # Process each result
    #     for row in results:
    #         # Remove prefix 'answer_' from node_id
    #         modified_node_id = row.node_id.replace('answer_', '')
    #         self.logger.info(f"return_gpt_agent_answer_to_graph, modified_node_id: {modified_node_id}")
    #
    #         # Check if this modified_node_id exists in graph_data
    #         matching_node = next((node for node in graph_data['nodes'] if node['id'] == modified_node_id), None)
    #         self.logger.info(f"return_gpt_agent_answer_to_graph, matching_node: {matching_node}")
    #         if matching_node:
    #             # Add a new edge if matching node is found
    #             new_edge = {
    #                 'from': matching_node['id'],
    #                 'to': f'answer_{row.node_id}',
    #                 'label': row.label
    #             }
    #             self.logger.info(f"return_gpt_agent_answer_to_graph, new_edge: {new_edge}")
    #             graph_data['edges'].append(new_edge)
    #             self.logger.info(f"return_gpt_agent_answer_to_graph, graph_data: {graph_data}")
    #         else:
    #             # Continue searching for other matches if no match is found
    #             continue
    #
    #     # Return updated graph_data or a message if no matches are found
    #     if not any('answer_' in edge['to'] for edge in graph_data['edges']):
    #         return "No matching nodes found in graph data for the provided node IDs."
    #
    #     return graph_data

    def return_gpt_agent_answer_to_graph(self, graph_data):
        node_answers_tbl_id = f"{self.bq_handler.bigquery_client.project}.{os.getenv('ANSWER_CURATED_CHAT_COMPLETIONS')}.{self.key}"

        # node_answers_tbl_id = f"{self.bq_handler.bigquery_client.project}.{os.getenv('ANSWER_CURATED_CHAT_COMPLETIONS')}.20231126125746_3f77f8f3-fd76-48d1-b28c-03054e6c3a06"

        query = f"""
        SELECT DISTINCT answer_node.node_id, answer_node.label
        FROM `{node_answers_tbl_id}`
        """

        # Execute the query
        query_job = self.bq_handler.bigquery_client.query(query)
        results = query_job.result()

        # Process each result
        for row in results:
            # Remove prefix 'answer_' from node_id
            modified_node_id = row.node_id.replace('answer_', '')
            matching_node = next((node for node in graph_data['nodes'] if node['id'] == modified_node_id), None)

            if matching_node:
                # Add a new node for the answer
                new_node = {
                    'id': row.node_id,  # Use the node_id from the query
                    'label': row.label
                }
                graph_data['nodes'].append(new_node)

                # Add a new edge connecting the matching node to the new node
                new_edge = {
                    'from': matching_node['id'],
                    'to': row.node_id  # Connect to the new node
                }
                graph_data['edges'].append(new_edge)

        return graph_data

    def setup_routes(self):
        self.app.route('/')(self.index_call)
        self.app.route('/get-graph-data', methods=['POST'])(self.get_graph_data)
        self.app.route('/get-available-graphs', methods=['GET'])(self.get_available_graphs)
        self.app.route('/return-gpt-agent-answer-to-graph', methods=['POST'])(self.matrix_sudoku_approach)
        # self.app.route('/return-gpt-agent-answer-to-graph', methods=['POST'])(self.engine_room.main_tree_based_design_general)
        # self.app.route('/save-graph', methods=['POST'])(self.save_graph)
        self.app.route('/save-graph', methods=['POST'])(self.matrix_sudoku_approach)

    def run(self):
        self.app.run(debug=True)


if __name__ == '__main__':
    server = App()
    server.run()