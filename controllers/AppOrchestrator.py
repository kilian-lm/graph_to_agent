import os
import datetime
# from flask import Flask, render_template, jsonify, request
import uuid
import logging
import json
import random
import re

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


# app = Flask(__name__)


class AppOrchestrator():
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
        self.gpt_agent_interactions = GptAgentInteractions(self.key)
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

        # self.app = Flask(__name__)
        # self.setup_routes()

    # def index_call(self):
    #     return render_template('graph.html')

    def get_graph_data(self, graph_id):
        try:
            # graph_id = request.json['graph_id']
            graph_data = self.gpt_agent_interactions.load_graph_data_by_id(graph_id)
            # return jsonify(graph_data)
            return graph_data
        except Exception as e:
            self.logger.error(f"Error fetching graph data: {e}")
            # return jsonify({"status": "error", "message": str(e)})

    def get_available_graphs(self):
        try:
            available_graphs = self.gpt_agent_interactions.get_available_graphs()
            # return jsonify(available_graphs)
            return available_graphs
        except Exception as e:
            self.logger.error(f"Error loading available graphs: {e}")
            # return jsonify({"status": "error", "message": str(e)})

    def save_graph(self, graph_data):
        try:
            # graph_data = request.json
            self.logger.info(f"save_graph, graph_data: {graph_data}")

            # graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            self.logger.info(f"save_graph, graph_id: {self.timestamp}")
            msg = self.gpt_agent_interactions.save_graph_data(graph_data, self.key)
            self.logger.info(msg)
            # self.logger.error(f"save_graph, errors: {errors}")
            #
            # if errors:
            #     return jsonify({"status": "error", "message": "Failed to save some data.", "errors": errors})

            # return jsonify({"status": "success", "message": 200})
        except Exception as e:
            self.logger.error(f"Error saving graph: {e}")
            # return jsonify({"status": "error", "message": str(e)})

    def matrix_sudoku_approach(self, graph_data):

        # graph_data = request.json
        self.logger.info(f"save_graph, graph_data: {graph_data}")

        key = self.key

        gpt_agent_interactions = GptAgentInteractions(key)

        gpt_agent_interactions.save_graph_data(graph_data, key)

        matrix_layer_one = MatrixLayerOne(key, graph_data, os.getenv('MULTI_LAYERED_MATRIX_DATASET_ID'))

        filename = matrix_layer_one.create_advanced_adjacency_matrix()
        # filename

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

        # Select a random answer node and save it
        random_answer = self.select_random_answer_nodes(graph_data)
        self.bq_handler.save_selected_answer(self.key, random_answer)

        return graph_data

    # def select_random_answer_nodes(self, graph_data):
    #     answer_nodes = [node for node in graph_data['nodes'] if node['id'].startswith('answer_')]
    #     if not answer_nodes:
    #         return "No answer nodes available"
    #
    #     selected_node = random.choice(answer_nodes)
    #     return selected_node['label']

    def clean_word(self, word):
        """Remove special characters and return the cleaned word."""
        return re.sub(r'\W+', '', word)

    def select_random_answer_nodes(self, graph_data):
        answer_nodes = [node for node in graph_data['nodes'] if node['id'].startswith('answer_')]
        num_nodes = min(len(answer_nodes), 5)  # Select up to 5 nodes

        selected_nodes = random.sample(answer_nodes, num_nodes)  # Select unique nodes

        common_fill_words = set(["to", "the", "a", "an", "and", "or", "but", "is", "of", "on", "in", "for"])
        used_words = set()
        words = []
        for node in selected_nodes:
            node_words = [self.clean_word(word) for word in node['label'].split() if
                          word.lower() not in common_fill_words]
            for word in node_words:
                if word not in used_words:
                    used_words.add(word)
                    words.append(word)
                    break  # Break after adding the first unique suitable word from this node

        return '_'.join(words)

    # def setup_routes(self):
    #     self.app.route('/')(self.index_call)
    #     self.app.route('/get-graph-data', methods=['POST'])(self.get_graph_data)
    #     self.app.route('/get-available-graphs', methods=['GET'])(self.get_available_graphs)
    #     self.app.route('/return-gpt-agent-answer-to-graph', methods=['POST'])(self.matrix_sudoku_approach)
    #     # self.app.route('/return-gpt-agent-answer-to-graph', methods=['POST'])(self.engine_room.main_tree_based_design_general)
    #     # self.app.route('/save-graph', methods=['POST'])(self.save_graph)
    #     self.app.route('/save-graph', methods=['POST'])(self.matrix_sudoku_approach)

#     def run(self):
#         self.app.run(debug=True)
#
#
# if __name__ == '__main__':
#     server = App()
#     server.run()
