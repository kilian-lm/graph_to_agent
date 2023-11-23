import os
import json
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
import logging
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google.cloud import bigquery
import json
import datetime
import requests
import inspect
import re
from google.api_core.exceptions import NotFound
import numpy as np

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

from logger.CustomLogger import CustomLogger
from controllers.BigQueryHandler import BigQueryHandler
from sql_queries.adjacency_matrix_query import ADJACENCY_MATRIX_QUERY
from sql_queries.edges_query import EDGES_QUERY
from sql_queries.nodes_query import NODES_QUERY
from sql_queries.layer_find_variable import LAYER_FIND_VARIABLE

from sql_queries.gpt_call_blueprint import GPT_CALL_BLUEPRINT

load_dotenv()


class AnswerPatternProcessor:
    def __init__(self, timestamp, gpt_calls_dataset_id):
        # self.timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        self.timestamp = timestamp
        print(self.timestamp)
        self.log_file = f'{self.timestamp}_answer_pattern_processor.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.openai_api_key}'
        }
        # todo: hand form app.py graph_id , think about coherent logic to ident nodes with matrix
        # self.graph_id = graph_id
        # self.table_name = self.graph_id

        # self.graph_data = graph_data

        self.bq_response_json = None
        self.variable_uuid_dict = None
        self.data = None
        self.gpt_blueprint = None
        self.gpt_calls_dataset_id = gpt_calls_dataset_id
        self.bq_handler = BigQueryHandler(self.timestamp, self.gpt_calls_dataset_id)

    def get_gpt_calls_blueprint(self):
        # table_ref = self.bq_handler.bigquery_client.dataset(self.gpt_calls_dataset_id).table(self.nodes_tbl)

        table_ref = "enter-universes.graph_to_agent_chat_completions.test_2"

        self.logger.info(table_ref)
        query = GPT_CALL_BLUEPRINT.format(
            tbl_ref=table_ref, graph_id=self.timestamp)

        self.logger.info(query)

        query_job = self.bq_handler.bigquery_client.query(query)

        df = query_job.to_dataframe()

        return df

    def get_sorted_variable_rows(self, df):
        # Filter rows with strings in the 'answer_label' column that start with '@var'
        filtered_df = df[df['answer_label'].str.startswith('@var')]
        self.logger.info(filtered_df)
        # Extract the suffixes and sort
        filtered_df['suffix_1'] = filtered_df['answer_label'].str.extract(r'@var(?:iable|ibale)_([0-9]+)')[0].astype(
            int)
        filtered_df['suffix_2'] = filtered_df['answer_label'].str.extract(r'@var(?:iable|ibale)_[0-9]+_([0-9]+)')[
            0].astype(int)
        sorted_df = filtered_df.sort_values(by=['suffix_1', 'suffix_2'])
        self.logger.info(sorted_df)
        # Return the ordered suffixes and uuids as a dict
        result_dict = dict(zip(sorted_df['uuid'], sorted_df['answer_label']))
        self.logger.info(result_dict)
        return result_dict

    def process_gpt_request_for_uuid(self, data, uuid):
        """Process GPT request for a specific UUID and update the DataFrame."""
        group = data[data['uuid'] == uuid]
        self.logger.info(group)
        messages = [{"role": r["role"], "content": r["content"]} for _, r in group.iterrows()]
        self.logger.info(messages)
        model = group.iloc[0]['model']

        self.logger.info(model)

        request_data = {
            "model": model,
            "messages": messages
        }
        self.logger.info(request_data)
        response = requests.post(self.openai_base_url, headers=self.headers, json=request_data)
        self.logger.info(response)
        response_json = response.json()
        self.logger.info(response_json)
        table_id = self.append_to_jsonl(response_json, uuid)
        self.logger.info(table_id)
        self.dump_gpt_jsonl_to_bigquery(table_id, self.gpt_calls_dataset_id, table_id)

        response_content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Update the DataFrame with the response
        last_index = group.index[-1]
        data.at[last_index, 'answer_label'] = response_content

        self.bq_response_json = {"response": response_content, "uuid": uuid}

        return response_content

    def append_to_jsonl(self, response_content, uuid):
        jsonl_filename = f'gpt_answer_{uuid}_{self.timestamp}.jsonl'

        with open(jsonl_filename, 'a') as file:
            graph_id = str(self.data[self.data['uuid'] == uuid].iloc[0]['graph_id'])
            path_id = str(self.data[self.data['uuid'] == uuid].iloc[0]['uuid'])
            answer_node_id = self.data[self.data['uuid'] == uuid].iloc[0]['answer_node_id']

            # Ensure response_content is a properly formatted JSON
            if not isinstance(response_content, dict):
                response_content = json.loads(response_content)

            # Adding the new fields to the response_content
            response_content['graph_id'] = graph_id
            response_content['path_id'] = path_id
            response_content['answer_node_id'] = answer_node_id

            # Write the modified response_content to the file
            json.dump(response_content, file)
            file.write('\n')

        return jsonl_filename

    def dump_gpt_jsonl_to_bigquery(self, dataset_name, jsonl_filename):
        """Upload the JSONL data to BigQuery."""
        # client = bigquery.Client()

        self.bq_handler.create_dataset_if_not_exists(dataset_name)
        # test_name = "gpt_answer_8262cd2c-c5e5-4ad1-a418-0217131aba70_20231117163236.jsonl"
        # test_name.split(".")[0]
        table_id = jsonl_filename.split(".")[0]
        self.bq_handler.create_table_if_not_exists(table_id)

        table_id = f"{self.bq_handler.bigquery_client.project}.{dataset_name}.{table_id}"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        with open(jsonl_filename, "rb") as source_file:
            job = self.bq_handler.bigquery_client.load_table_from_file(
                source_file, table_id, job_config=job_config
            )
        job.result()

    def run(self):
        # Get the GPT calls blueprint
        self.data = self.get_gpt_calls_blueprint()
        self.logger.info(self.data)
        # Get the sorted variables
        self.variable_uuid_dict = self.get_sorted_variable_rows(self.data)
        # Sort the dictionary by variable suffixes in ascending order
        sorted_variables = sorted(self.variable_uuid_dict.items(),
                                  key=lambda x: [int(num) for num in x[1].split('_')[1:]])

        # Process each variable
        for i in range(len(sorted_variables) - 1):
            lower_var_uuid, lower_var_label = sorted_variables[i]
            self.logger.info(lower_var_uuid)
            higher_var_uuid, higher_var_label = sorted_variables[i + 1]
            self.logger.info(higher_var_uuid)
            # Process the lower variable
            lower_response = self.process_gpt_request_for_uuid(self.data, lower_var_uuid)
            self.data['answer_label'] = self.data['answer_label'].apply(
                lambda x: x.replace(lower_var_label, lower_response))
            self.logger.info(self.data['answer_label'])
            self.data['content'] = self.data['content'].apply(lambda x: x.replace(lower_var_label, lower_response))
            self.logger.info(self.data['content'])
            # Update the higher variable in 'content' with the lower response
            self.data['content'] = self.data['content'].apply(lambda x: x.replace(higher_var_label, lower_response))

        # Process the highest variable
        highest_var_uuid, highest_var_label = sorted_variables[-1]
        self.logger.info(highest_var_uuid)
        highest_response = self.process_gpt_request_for_uuid(self.data, highest_var_uuid)
        self.logger.info(highest_response)
        self.data['answer_label'] = self.data['answer_label'].apply(
            lambda x: x.replace(highest_var_label, highest_response))
        self.data['content'] = self.data['content'].apply(lambda x: x.replace(highest_var_label, highest_response))
        self.logger.info(self.data['content'])
        # Process rows with 'None' in 'answer_label'
        none_rows = self.data[self.data['answer_label'] == 'None']
        for idx, row in none_rows.iterrows():
            response = self.process_gpt_request_for_uuid(self.data, row['uuid'])
            self.logger.info(response)
            self.data.at[idx, 'answer_label'] = response

        self.logger.info(self.data.info())

        self.transform_and_load_to_bigquery(self.data, self.gpt_calls_dataset_id, "test_20231122")

        return self.data

    def transform_and_load_to_bigquery(self, df, dataset_name, table_id):
        # Transform DataFrame to match the BigQuery schema
        df['answer_node'] = df.apply(lambda row: {'label': row['answer_label'], 'node_id': row['answer_node_id']},
                                     axis=1)
        df['gpt_call'] = df.apply(
            lambda row: {'messages': [{'content': row['content'], 'role': row['role']}], 'model': row['model']}, axis=1)

        # Select only the columns that match the BigQuery table structure
        df = df[['graph_id', 'uuid', 'answer_node', 'gpt_call']]

        table_id = f"{self.bq_handler.bigquery_client.project}.{dataset_name}.{table_id}"

        # Define job configuration
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True,
        )

        # Load the DataFrame into BigQuery
        job = self.bq_handler.bigquery_client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for the job to complete

        print(f"Loaded {job.output_rows} rows into {table_id}")


# answer_pat_pro = AnswerPatternProcessor("20231117163236", "graph_to_agent_chat_completions")
#
# answer_pat_pro.bq_handler.create_dataset_if_not_exists()
#
# answer_pat_pro.dump_gpt_jsonl_to_bigquery("gpt_answer_8262cd2c-c5e5-4ad1-a418-0217131aba70_20231117163236.jsonl",
#                                           "graph_to_agent_chat_completions",
#                                           "gpt_answer_8262cd2c-c5e5-4ad1-a418-0217131aba70_20231117163236")
#
# answer_pat_pro.run()

# import uuid
# from controllers.MatrixLayerOne import MatrixLayerOne
#
# from controllers.GraphPatternProcessor import GraphPatternProcessor
#
# from controllers.MatrixLayerTwo import MatrixLayerTwo
# from controllers.v2GptAgentInteractions import v2GptAgentInteractions
#
# timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
# general_uuid = str(uuid.uuid4())
# key = f"{timestamp}_{general_uuid}"
#
# json_file_path = "./logics/simple_va_inheritance_20231117.json"
#
# with open(json_file_path, 'r') as json_file:
#     graph_data = json.load(json_file)
#
# gpt_agent_interactions = v2GptAgentInteractions(key, os.getenv('GRAPH_DATASET_ID'))
#
# gpt_agent_interactions.save_graph_data(graph_data, key)
#
# # self.graph_to_agent_adjacency_matrices = "graph_to_agent_adjacency_matrices"
# # graph_data = graph_data
# # matrix_layer_one = MatrixLayerOne(timestamp, graph_data, matrix_layer_one_dataset_id)
# #
# # self.matrix_layer_one.upload_to_bigquery()
#
#
# matrix_layer_one = MatrixLayerOne(key, graph_data, os.getenv('MULTI_LAYERED_MATRIX_DATASET_ID'))
#
# filename = matrix_layer_one.create_advanced_adjacency_matrix()
# matrix_layer_one.upload_jsonl_to_bigquery(filename, os.getenv('MULTI_LAYERED_MATRIX_DATASET_ID'))
#
# filename = matrix_layer_one.upload_to_bigquery(os.getenv('ADJACENCY_MATRIX_DATASET_ID'))
# # matrix_layer_one.upload_jsonl_to_bigquery(os.getenv('ADJACENCY_MATRIX_DATASET_ID'), filename)
#
# # '20231117163236_advanced_adjacency_matrix.jsonl'
# mat_l_t = MatrixLayerTwo(key, os.getenv('ADJACENCY_MATRIX_DATASET_ID'), os.getenv('GRAPH_DATASET_ID'))
#
# mat_l_t.get_edges()
# mat_l_t.get_nodes()
# mat_l_t.get_adjacency_matrix()
#
# df = mat_l_t.get_adjacency_matrix().set_index("node_id")
# G = mat_l_t.create_graph_from_adjacency(df)
# G.number_of_edges()
#
# df_nodes = mat_l_t.get_nodes()
# label_dict = df_nodes.set_index('id')['label'].to_dict()
# nx.set_node_attributes(G, label_dict, 'label')
#
# # ToDo :: Continue here
#
# graph_pattern_processor = GraphPatternProcessor(key, os.getenv('ADJACENCY_MATRIX_DATASET_ID'),
#                                                 os.getenv('GRAPH_DATASET_ID'),
#                                                 G, os.getenv('NUM_STEPS'))
#
# filename = f'{key}_multi_layered_matrix.jsonl'
# graph_pattern_processor.save_gpt_calls_to_jsonl(filename, key)
#
# graph_pattern_processor.dump_to_bigquery(filename, os.getenv('CURATED_CHAT_COMPLETIONS'), key)
#
# answer_pat_pro = AnswerPatternProcessor("20231117163236", "graph_to_agent_chat_completions")
#
# answer_pat_pro.bq_handler.create_dataset_if_not_exists()
#
# answer_pat_pro.dump_gpt_jsonl_to_bigquery("gpt_answer_8262cd2c-c5e5-4ad1-a418-0217131aba70_20231117163236.jsonl",
#                                           "graph_to_agent_chat_completions",
#                                           "gpt_answer_8262cd2c-c5e5-4ad1-a418-0217131aba70_20231117163236")
#
# answer_pat_pro.run()
