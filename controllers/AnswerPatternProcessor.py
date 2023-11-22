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

        # Extract the suffixes and sort
        filtered_df['suffix_1'] = filtered_df['answer_label'].str.extract(r'@var(?:iable|ibale)_([0-9]+)')[0].astype(
            int)
        filtered_df['suffix_2'] = filtered_df['answer_label'].str.extract(r'@var(?:iable|ibale)_[0-9]+_([0-9]+)')[
            0].astype(int)
        sorted_df = filtered_df.sort_values(by=['suffix_1', 'suffix_2'])

        # Return the ordered suffixes and uuids as a dict
        result_dict = dict(zip(sorted_df['uuid'], sorted_df['answer_label']))
        return result_dict

    def process_gpt_request_for_uuid(self, data, uuid):
        """Process GPT request for a specific UUID and update the DataFrame."""
        group = data[data['uuid'] == uuid]
        messages = [{"role": r["role"], "content": r["content"]} for _, r in group.iterrows()]
        model = group.iloc[0]['model']

        request_data = {
            "model": model,
            "messages": messages
        }
        response = requests.post(self.openai_base_url, headers=self.headers, json=request_data)
        response_json = response.json()

        self.append_to_jsonl(response_json, uuid)

        response_content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Update the DataFrame with the response
        last_index = group.index[-1]
        data.at[last_index, 'answer_label'] = response_content

        self.bq_response_json = {"response": response_content, "uuid": uuid}

        return response_content

    def append_to_jsonl(self, response_content, uuid):

        jsonl_filename = f'gpt_answer_{uuid}_{self.timestamp}.jsonl'

        with open(jsonl_filename, 'a') as file:
            graph_id = self.data[self.data['uuid'] == uuid].iloc[0]['graph_id']
            answer_node_id = self.data[self.data['uuid'] == uuid].iloc[0]['answer_node_id']

            enriched_response = {
                "graph_id": graph_id,
                "uuid": uuid,
                "answer_node_id": answer_node_id,
                "response": response_content
            }

            json.dump(enriched_response, file)
            file.write('\n')
        return jsonl_filename

    def dump_gpt_jsonl_to_bigquery(self, file_path, dataset_name, jsonl_filename):
        """Upload the JSONL data to BigQuery."""
        # client = bigquery.Client()

        self.bq_handler.create_dataset_if_not_exists()
        self.bq_handler.create_table_if_not_exists(jsonl_filename)

        table_id = f"{self.bq_handler.bigquery_client.project}.{dataset_name}.{jsonl_filename}"
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
            higher_var_uuid, higher_var_label = sorted_variables[i + 1]

            # Process the lower variable
            lower_response = self.process_gpt_request_for_uuid(lower_var_uuid)
            self.data['answer_label'] = self.data['answer_label'].apply(
                lambda x: x.replace(lower_var_label, lower_response))
            self.data['content'] = self.data['content'].apply(lambda x: x.replace(lower_var_label, lower_response))

            # Update the higher variable in 'content' with the lower response
            self.data['content'] = self.data['content'].apply(lambda x: x.replace(higher_var_label, lower_response))

        # Process the highest variable
        highest_var_uuid, highest_var_label = sorted_variables[-1]
        highest_response = self.process_gpt_request_for_uuid(highest_var_uuid)
        self.data['answer_label'] = self.data['answer_label'].apply(
            lambda x: x.replace(highest_var_label, highest_response))
        self.data['content'] = self.data['content'].apply(lambda x: x.replace(highest_var_label, highest_response))

        # Process rows with 'None' in 'answer_label'
        none_rows = self.data[self.data['answer_label'] == 'None']
        for idx, row in none_rows.iterrows():
            response = self.process_gpt_request_for_uuid(row['uuid'])
            self.data.at[idx, 'answer_label'] = response

        return self.data
