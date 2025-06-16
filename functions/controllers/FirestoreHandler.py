import os
import json
import logging
import datetime
import re
import firebase_admin
from firebase_admin import credentials, firestore
import openai
import requests

from logger.CustomLogger import CustomLogger

class FirestoreHandler:
    def __init__(self, key):
        self.key = key
        self.log_file = f'{self.key}_firestore_handler.log'
        self.log_dir = './temp_log'
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_level = logging.DEBUG
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.openai_api_key}'
        }
        
        # Initialize Firestore client
        self.db = firestore.client()
        self.logger.info("Firestore client successfully initialized.")

    def save_selected_answer(self, graph_id, answer):
        try:
            # Reference to the collection
            collection_ref = self.db.collection('selected_answers')
            
            # Data to be saved
            data = {
                "graph_id": graph_id,
                "selected_answer": answer,
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            
            # Add the document
            collection_ref.add(data)
            
            return {"status": "success", "message": "Selected answer saved successfully"}
        except Exception as e:
            self.logger.error(f"Encountered errors while inserting the selected answer: {e}")
            return {"status": "error", "message": "Failed to save the selected answer"}

    def translate_graph_data_for_firestore(self, graph_data, graph_id):
        # Extract nodes and edges from the graph data
        raw_nodes = graph_data.get('nodes', [])
        raw_edges = graph_data.get('edges', [])

        # Translate nodes
        nodes_for_fs = [
            {
                "graph_id": graph_id,
                "id": node.get('id'),
                "label": node.get('label')
            }
            for node in raw_nodes
        ]

        self.logger.debug(f"nodes_for_fs: {nodes_for_fs}")

        # Translate edges
        edges_for_fs = [
            {
                "graph_id": graph_id,
                "from": edge.get('from'),
                "to": edge.get('to')
            }
            for edge in raw_edges
        ]

        self.logger.debug(f"edges_for_fs: {edges_for_fs}")

        return nodes_for_fs, edges_for_fs

    def save_graph_data(self, graph_data, graph_id):
        try:
            # Use the translator function to transform the data
            nodes_for_fs, edges_for_fs = self.translate_graph_data_for_firestore(graph_data, graph_id)

            # Log the transformed data for debugging
            self.logger.debug(f"Transformed Nodes: {nodes_for_fs}")
            self.logger.debug(f"Transformed Edges: {edges_for_fs}")

            # Save nodes to Firestore
            nodes_batch = self.db.batch()
            nodes_collection = self.db.collection('nodes')
            for node in nodes_for_fs:
                doc_ref = nodes_collection.document()
                nodes_batch.set(doc_ref, node)
            nodes_batch.commit()

            # Save edges to Firestore
            edges_batch = self.db.batch()
            edges_collection = self.db.collection('edges')
            for edge in edges_for_fs:
                doc_ref = edges_collection.document()
                edges_batch.set(doc_ref, edge)
            edges_batch.commit()

            # Save the transformed data as dictionaries for the workflow
            graph_data_as_dicts = {
                "nodes": nodes_for_fs,
                "edges": edges_for_fs
            }

            self.logger.debug(f"graph_data_as_dicts: {graph_data_as_dicts}")

            return {"status": "success", "savedGraph": graph_data_as_dicts}

        except Exception as e:
            self.logger.exception(f"An unexpected error occurred during save_graph_data: {e}")
            raise

    def load_graph_data_by_id(self, graph_id):
        try:
            # Query nodes for given graph_id
            nodes_query = self.db.collection('nodes').where('graph_id', '==', graph_id).stream()
            nodes = [{"id": doc.get('id'), "label": doc.get('label')} for doc in nodes_query]

            self.logger.info(f"nodes loaded by graph id {nodes}")

            # Query edges for given graph_id
            edges_query = self.db.collection('edges').where('graph_id', '==', graph_id).stream()
            edges = [{"from": doc.get('from'), "to": doc.get('to')} for doc in edges_query]

            return {"nodes": nodes, "edges": edges}
        except Exception as e:
            self.logger.error(f"Error loading graph data: {e}")
            raise

    def get_available_graphs(self):
        try:
            # Query to get distinct graph_ids from the nodes collection
            nodes_ref = self.db.collection('nodes')
            graph_ids = set()
            
            # Get all documents and extract unique graph_ids
            docs = nodes_ref.stream()
            for doc in docs:
                graph_id = doc.get('graph_id')
                if graph_id:
                    graph_ids.add(graph_id)
            
            return [{"graph_id": graph_id, "graph_name": graph_id} for graph_id in graph_ids]
        except Exception as e:
            self.logger.error(f"Error getting available graphs: {e}")
            raise

    def save_adjacency_matrix(self, matrix_data, dataset_id):
        try:
            # Save adjacency matrix to Firestore
            matrix_collection = self.db.collection('adjacency_matrices')
            
            # Create a document with the dataset_id and key
            doc_ref = matrix_collection.document(f"{dataset_id}_{self.key}")
            doc_ref.set({
                "dataset_id": dataset_id,
                "key": self.key,
                "matrix_data": matrix_data,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            
            return {"status": "success", "message": "Adjacency matrix saved successfully"}
        except Exception as e:
            self.logger.error(f"Error saving adjacency matrix: {e}")
            raise

    def save_multi_layered_matrix(self, matrix_data, dataset_id):
        try:
            # Save multi-layered matrix to Firestore
            matrix_collection = self.db.collection('multi_layered_matrices')
            
            # Create a document with the dataset_id and key
            doc_ref = matrix_collection.document(f"{dataset_id}_{self.key}")
            doc_ref.set({
                "dataset_id": dataset_id,
                "key": self.key,
                "matrix_data": matrix_data,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            
            return {"status": "success", "message": "Multi-layered matrix saved successfully"}
        except Exception as e:
            self.logger.error(f"Error saving multi-layered matrix: {e}")
            raise

    def save_gpt_calls(self, gpt_calls_data, collection_name):
        try:
            # Save GPT calls to Firestore
            gpt_calls_collection = self.db.collection(collection_name)
            
            # Use a batch write for efficiency
            batch = self.db.batch()
            
            for call_data in gpt_calls_data:
                doc_ref = gpt_calls_collection.document()
                # Add key to the data
                call_data['key'] = self.key
                call_data['timestamp'] = firestore.SERVER_TIMESTAMP
                batch.set(doc_ref, call_data)
            
            # Commit the batch
            batch.commit()
            
            return {"status": "success", "message": f"GPT calls saved to {collection_name} successfully"}
        except Exception as e:
            self.logger.error(f"Error saving GPT calls to {collection_name}: {e}")
            raise