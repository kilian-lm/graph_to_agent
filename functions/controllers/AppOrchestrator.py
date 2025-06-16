import os
import datetime
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
from controllers.FirestoreHandler import FirestoreHandler

from dotenv import load_dotenv

load_dotenv()

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
        self.firestore_handler = FirestoreHandler(self.key)

        # All Checkpoints and Externalities
        self.logs_bucket = os.getenv('LOGS_BUCKET')
        self.edges_table = os.getenv('EDGES_TABLE')
        self.nodes_table = os.getenv('NODES_TABLE')
        self.matrix_dataset_id = os.getenv('MATRIX_DATASET_ID')
        self.graph_dataset_id = os.getenv('GRAPH_DATASET_ID')
        self.graph = None
        self.num_steps = os.getenv('NUM_STEPS')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = os.getenv('OPENAI_BASE_URL')

    def get_graph_data(self, graph_id):
        try:
            # Use FirestoreHandler instead of BigQueryHandler
            graph_data = self.firestore_handler.load_graph_data_by_id(graph_id)
            return graph_data
        except Exception as e:
            self.logger.error(f"Error fetching graph data: {e}")
            raise

    def get_available_graphs(self):
        try:
            # Use FirestoreHandler instead of BigQueryHandler
            available_graphs = self.firestore_handler.get_available_graphs()
            return available_graphs
        except Exception as e:
            self.logger.error(f"Error loading available graphs: {e}")
            raise

    def save_graph(self, graph_data):
        try:
            self.logger.info(f"save_graph, graph_data: {graph_data}")
            self.logger.info(f"save_graph, graph_id: {self.timestamp}")
            
            # Use FirestoreHandler instead of BigQueryHandler
            msg = self.firestore_handler.save_graph_data(graph_data, self.key)
            self.logger.info(msg)
        except Exception as e:
            self.logger.error(f"Error saving graph: {e}")
            raise

    def matrix_sudoku_approach(self, graph_data):
        try:
            self.logger.info(f"matrix_sudoku_approach, graph_data: {graph_data}")
            
            key = self.key
            
            # Save graph data
            self.firestore_handler.save_graph_data(graph_data, key)
            
            # Create and save adjacency matrix
            matrix_layer_one = MatrixLayerOne(key, graph_data, os.getenv('MULTI_LAYERED_MATRIX_DATASET_ID'))
            filename = matrix_layer_one.create_advanced_adjacency_matrix()
            
            # Save matrices to Firestore
            with open(filename, 'r') as f:
                matrix_data = json.load(f)
                self.firestore_handler.save_multi_layered_matrix(matrix_data, os.getenv('MULTI_LAYERED_MATRIX_DATASET_ID'))
            
            # Process graph patterns and save GPT calls
            graph_processor = GraphPatternProcessor(10, key)
            gpt_calls_data = graph_processor.save_gpt_calls_to_jsonl(key)
            self.firestore_handler.save_gpt_calls(gpt_calls_data, 'curated_chat_completions')
            
            # Process answer patterns
            answer_pat_pro = AnswerPatternProcessor(key)
            answer_data = answer_pat_pro.run()
            self.firestore_handler.save_gpt_calls(answer_data, 'answer_curated_chat_completions')
            
            # Return updated graph
            graph_data = self.return_gpt_agent_answer_to_graph(graph_data)
            
            return graph_data
        except Exception as e:
            self.logger.error(f"Error in matrix sudoku approach: {e}")
            raise

    def return_gpt_agent_answer_to_graph(self, graph_data):
        try:
            # Query Firestore for answer nodes
            answer_collection = self.firestore_handler.db.collection('answer_curated_chat_completions')
            answer_query = answer_collection.where('key', '==', self.key).stream()
            
            # Process each result
            for doc in answer_query:
                data = doc.to_dict()
                node_id = data.get('node_id')
                label = data.get('label')
                
                if node_id and label:
                    # Remove prefix 'answer_' from node_id
                    modified_node_id = node_id.replace('answer_', '')
                    matching_node = next((node for node in graph_data['nodes'] if node['id'] == modified_node_id), None)
                    
                    if matching_node:
                        # Add a new node for the answer
                        new_node = {
                            'id': node_id,
                            'label': label
                        }
                        graph_data['nodes'].append(new_node)
                        
                        # Add a new edge connecting the matching node to the new node
                        new_edge = {
                            'from': matching_node['id'],
                            'to': node_id
                        }
                        graph_data['edges'].append(new_edge)
            
            # Select a random answer node and save it
            random_answer = self.select_random_answer_nodes(graph_data)
            self.firestore_handler.save_selected_answer(self.key, random_answer)
            
            return graph_data
        except Exception as e:
            self.logger.error(f"Error in return_gpt_agent_answer_to_graph: {e}")
            raise

    def clean_word(self, word):
        """Remove special characters and return the cleaned word."""
        return re.sub(r'\W+', '', word)

    def select_random_answer_nodes(self, graph_data):
        answer_nodes = [node for node in graph_data['nodes'] if node['id'].startswith('answer_')]

        # Randomly shuffle the answer nodes to get a varied selection each time
        random.shuffle(answer_nodes)

        common_fill_words = set(["to", "the", "a", "an", "and", "or", "but", "is", "of", "on", "in", "for"])
        used_words = set()
        words = []

        for node in answer_nodes:
            node_words = [self.clean_word(word) for word in node['label'].split() if
                          word.lower() not in common_fill_words]
            added_words = 0
            for word in node_words:
                if word not in used_words:
                    used_words.add(word)
                    words.append(word)
                    added_words += 1
                    if added_words >= 3:
                        break  # Break after adding at least 3 unique suitable words from this node

        # Concatenate words, ensuring the length does not exceed 70 characters
        random_answer = ''
        for word in words:
            if len(random_answer) + len(word) + 1 <= 70:  # +1 for the underscore
                random_answer += (word + '_')
            else:
                break

        return random_answer.strip('_')  # Remove trailing underscore