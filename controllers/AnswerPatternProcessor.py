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

    def extract_variables(self, content):
        """Extract @variable tags from the content."""
        return re.findall(r"@variable_\d+_\d+", content)

    def process_gpt_request_for_uuid(self, uuid):
        """Process GPT request for a specific UUID and update the gpt_blueprintFrame."""
        group = self.gpt_blueprint[self.gpt_blueprint['uuid'] == uuid]
        messages = [{"role": r["role"], "content": r["content"]} for _, r in group.iterrows()]
        model = group.iloc[0]['model']

        # Send GPT request
        request_data = {
            "model": model,
            "messages": messages
        }
        response = requests.post(self.open_ai_url, headers=self.headers, json=request_data)
        response_json = response.json()
        response_content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Update the DataFrame with the response
        last_index = group.index[-1]
        self.gpt_blueprint.at[last_index, 'answer_label'] = response_content
        return response_content

    def process_variable_responses(self):
        """Process responses for each @variable in sorted order."""
        variable_tags = defaultdict(list)
        for index, row in self.gpt_blueprint.iterrows():
            variables = self.extract_variables(row['content'])
            for var in variables:
                variable_tags[var].append((row['uuid'], index))

        sorted_variables = sorted(variable_tags.keys(), key=lambda x: (int(x.split('_')[1]), int(x.split('_')[2])))

        variable_responses = {}
        for var in sorted_variables:
            uuids = set([uuid for uuid, _ in variable_tags[var]])
            for uuid in uuids:
                response = self.process_gpt_request_for_uuid(uuid)
                variable_responses[var] = response

            # Update the DataFrame with the response for this and higher suffix variables
            for higher_var in sorted_variables[sorted_variables.index(var) + 1:]:
                for higher_uuid, _ in variable_tags[higher_var]:
                    self.gpt_blueprint.loc[self.gpt_blueprint['uuid'] == higher_uuid, 'content'] = \
                    self.gpt_blueprint[self.gpt_blueprint['uuid'] == higher_uuid]['content'].apply(
                        lambda x: x.replace(var, variable_responses[var])
                    )


answer_pat_pro = AnswerPatternProcessor("20231117163236", "graph_to_agent_chat_completions")

answer_pat_pro.get_gpt_calls_blueprint()