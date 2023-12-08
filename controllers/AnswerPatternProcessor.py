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


from controllers.config import Config

load_dotenv()

# CACHE_DIRECTORY = '/cache'  # Directory where the API key will be stored
#
# def save_api_key(api_key):
#     # Create the /cache directory if it doesn't exist
#     if not os.path.exists(CACHE_DIRECTORY):
#         os.makedirs(CACHE_DIRECTORY)
#
#     # Write the API key to a JSON file in /cache
#     with open(os.path.join(CACHE_DIRECTORY, 'api_key.json'), 'w') as file:
#         json.dump({'api_key': api_key}, file)
#
# def get_api_key():
#     # Read the API key from the JSON file in /cache
#     api_key_file = os.path.join(CACHE_DIRECTORY, 'api_key.json')
#     if os.path.exists(api_key_file):
#         with open(api_key_file, 'r') as file:
#             data = json.load(file)
#             return data.get('api_key')
#     return None


class AnswerPatternProcessor:
    def __init__(self, key):
        self.key = key
        print(self.key)
        self.log_file = f'{self.key}_answer_pattern_processor.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

        # self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_api_key = get_api_key()
        self.openai_base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.openai_api_key}'
        }

        # Tbls
        self.raw_chat_completions = os.getenv('RAW_CHAT_COMPLETIONS')
        self.graph_to_agent_curated_chat_completions = os.getenv('CURATED_CHAT_COMPLETIONS')
        self.graph_to_agent_answer_curated_chat_completions = os.getenv('ANSWER_CURATED_CHAT_COMPLETIONS')

        # Dir
        self.temp_checkpoints_gpt_calls = os.getenv('TEMP_CHECKPOINTS_GPT_CALLS')
        self.temp_raw_chat_completions = os.getenv('TEMP_RAW_CHAT_COMPLETIONS_DIR')

        # Datasets
        self.bq_response_json = None
        self.variable_uuid_dict = None
        self.data = None
        self.gpt_blueprint = None

        self.bq_handler = BigQueryHandler(self.key)

    def get_gpt_calls_blueprint(self):
        # table_ref = self.bq_handler.bigquery_client.dataset(self.gpt_calls_dataset_id).table(self.nodes_tbl)

        # table_ref = "enter-universes.graph_to_agent_chat_completions.test_2"
        table_ref = f"enter-universes.{self.graph_to_agent_curated_chat_completions}.{self.key}"

        self.logger.info(table_ref)
        query = GPT_CALL_BLUEPRINT.format(
            tbl_ref=table_ref, graph_id=self.key)

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
        # todo :: include raw safe to bq
        self.raw_gpt_answer_dump_gpt_jsonl_to_bigquery(uuid)
        self.dump_gpt_jsonl_to_bigquery(self.key)

        response_content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Update the DataFrame with the response
        last_index = group.index[-1]
        data.at[last_index, 'answer_label'] = response_content

        self.bq_response_json = {"response": response_content, "uuid": uuid}

        return response_content

    def append_to_jsonl(self, response_content, uuid):
        """
        Appends a JSON-formatted response to a .jsonl file specific to a given UUID.
        This method checks if the directory for storing the file exists, creates it if not,
        and then appends the response to the file.

        The response content is enhanced with additional fields: 'graph_id', 'path_id',
        and 'answer_node_id' extracted from the instance's data attribute based on the UUID.

        Parameters:
        - response_content (dict or str): The content to be written to the file.
                                         Should be a dictionary or a JSON-formatted string.
        - uuid (str): Unique identifier used to generate the filename and extract additional data.

        Returns:
        - str: The path to the .jsonl file where the content was appended.
        """

        # Construct the directory path
        dir_path = self.temp_raw_chat_completions

        # Check if the directory exists, if not, create it
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # Construct the file path
        jsonl_filename = f'{dir_path}/gpt_answer_{uuid}_{self.key}.jsonl'

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

    def raw_gpt_answer_dump_gpt_jsonl_to_bigquery(self, path_uuid):
        """Upload raw_gpt_answerthe JSONL data to BigQuery."""

        file_path = f'{self.temp_raw_chat_completions}/gpt_answer_{path_uuid}_{self.key}.jsonl'

        self.bq_handler.create_dataset_if_not_exists(self.raw_chat_completions)
        # test_name = "gpt_answer_8262cd2c-c5e5-4ad1-a418-0217131aba70_20231117163236.jsonl"
        # test_name.split(".")[0]
        # table_id = path_uuid
        self.bq_handler.create_table_if_not_exists(self.raw_chat_completions, path_uuid)

        table_id = f"{self.bq_handler.bigquery_client.project}.{self.raw_chat_completions}.{path_uuid}"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        with open(file_path, "rb") as source_file:
            job = self.bq_handler.bigquery_client.load_table_from_file(
                source_file, table_id, job_config=job_config
            )
        job.result()

    def transform_record(self, record):
        """
        Transforms a record from the JSONL format to the BigQuery schema.
        """
        transformed = {
            'graph_id': record.get('graph_id'),
            'uuid': record.get('uuid'),
            'answer_node': {
                'label': record.get('answer_node', {}).get('label'),
                'node_id': record.get('answer_node', {}).get('node_id')
            },
            'gpt_call': {
                'model': record.get('gpt_call', {}).get('model'),
                'messages': record.get('gpt_call', {}).get('messages', [])
            },
            'path': record.get('path', [])
        }
        return transformed

    def load_to_bigquery(self, data, table_id):
        """
        Loads data to a BigQuery table.
        """

        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("graph_id", "STRING"),
                bigquery.SchemaField("uuid", "STRING"),
                bigquery.SchemaField("answer_node", "RECORD", fields=[
                    bigquery.SchemaField("label", "STRING"),
                    bigquery.SchemaField("node_id", "STRING"),
                ]),
                bigquery.SchemaField("gpt_call", "RECORD", fields=[
                    bigquery.SchemaField("model", "STRING"),
                    bigquery.SchemaField("messages", "RECORD", mode="REPEATED", fields=[
                        bigquery.SchemaField("content", "STRING"),
                        bigquery.SchemaField("role", "STRING"),
                    ]),
                ]),
                bigquery.SchemaField("path", "STRING", mode="REPEATED")
            ],
            write_disposition="WRITE_TRUNCATE",
        )

        bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')

        bq_client_secrets_parsed = json.loads(bq_client_secrets)
        bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
        bq_client = bigquery.Client(credentials=bq_client_secrets,
                                    project=bq_client_secrets.project_id)

        job = bq_client.load_table_from_json(data, table_id, job_config=job_config)
        job.result()  # Wait for the job to complete

        if job.errors:
            raise Exception(f'BigQuery load error: {job.errors}')
        else:
            print(f'Loaded {len(data)} rows into {table_id}.')

        # Define your BigQuery table ID

    def dump_gpt_jsonl_to_bigquery(self, key):
        transformed_data = []
        self.logger.info(f'checking dir : {self.temp_checkpoints_gpt_calls}.{key}.jsonl')
        with open(f'{self.temp_checkpoints_gpt_calls}/{key}.jsonl', 'r') as file:
            for line in file:
                record = json.loads(line)
                transformed_data.append(self.transform_record(record))

        # Load data to BigQuery
        table_id = f"{self.bq_handler.bigquery_client.project}.{os.getenv('CURATED_CHAT_COMPLETIONS')}.{key}"
        self.load_to_bigquery(transformed_data, table_id)

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

        self.transform_and_load_to_bigquery(self.data, self.graph_to_agent_answer_curated_chat_completions, self.key)

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
