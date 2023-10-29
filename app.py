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

from app.Solver import Solver
from app.LoggerPublisher.MainPublisher import MainPublisher
from app.LoggerPublisher.MainLogger import MainLogger

load_dotenv()

import datetime
import json

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from google.cloud.exceptions import NotFound


class AgentModelerApp:
    def __init__(self, openai_api_key: str, url: str):
        self.app = Flask(__name__)
        self.app.secret_key = 'some_secret_key'
        self.setup_routes()
        self.openai_api_key = openai_api_key
        self.openai_base_url = url

        bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')

        bq_client_secrets_parsed = json.loads(bq_client_secrets)
        bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
        self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
        self.bigquery_client = bigquery.Client(credentials=self.bq_client_secrets,
                                               project=self.bq_client_secrets.project_id)
        self.project_id = self.bq_client_secrets.project_id
        self.project_id = "enter-universes"
        self.topic_id = "enter-universes"
        self.bucket_name = 'logs-graph-to-agents'
        # AWS parameters
        ACCESS_KEY = os.environ.get('ACCESS_KEY')
        SECRET_KEY = os.environ.get('SECRET_KEY')
        REGION = os.environ.get('REGION')

        log_dir = 'temp_log'

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file = f'{timestamp}_graph_to_agents.log'
        self.param_bucket_name = self.bucket_name
        self.logger = MainLogger(self.param_bucket_name, log_dir='temp_log', log_file=log_file)

        # Assuming you've set up logger and publisher already

        self.log_dir = 'temp_log'
        self.publisher = MainPublisher(project_id=self.project_id, topic_name=self.topic_id)

    # def _log_and_raise_error(self, method_name, e):
    #     error_msg = f'{self.__class__.__name__}.{method_name} encountered the Error: {str(e)}'
    #     self.logger.error(error_msg)
    #     self.publisher.publish_message(error_msg)
    #     raise Exception(e)

    def _data_to_jsonl(self, data):
        try:
            return '\n'.join(json.dumps(item) for item in data)
        except Exception as e:
            error_msg = f'{self.__class__.__name__}.{self._data_to_jsonl.__name__} encountered the Error: {str(e)}'
            self.logger.error(error_msg)
            self.publisher.publish_message(error_msg)
            raise Exception(e)

    def setup_routes(self):
        try:
            self.app.route('/')(self.index)
            self.app.route('/save_to_bigquery', methods=['POST'])(self.save_to_bigquery)
            self.app.route('/get_saved_setups', methods=['GET'])(self.get_saved_setups)
            self.app.route('/trigger_agent_pool', methods=['POST'])(self.trigger_agent_pool)
        except Exception as e:
            error_msg = f'{self.__class__.__name__}.{self.setup_routes.__name__} encountered the Error: {str(e)}'
            self.logger.error(error_msg)
            self.publisher.publish_message(error_msg)
            raise Exception(e)

    def index(self):
        try:
            return render_template('index.html')
        except Exception as e:
            error_msg = f'{self.__class__.__name__}.{self.setup_routes.__name__} encountered the Error: {str(e)}'
            self.logger.error(error_msg)
            self.publisher.publish_message(error_msg)
            raise Exception(e)

    def trigger_agent_pool(self):
        try:
            data = request.json
            table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"
            if not self._table_exists(table_id):
                self._create_table(table_id)

            timestamp_str = datetime.datetime.utcnow().isoformat()
            data_as_jsonl = self._data_to_jsonl(data)

            rows_to_insert = [{"timestamp": timestamp_str, "data": data_as_jsonl}]
            errors = self.bigquery_client.insert_rows_json(table_id, rows_to_insert)
            if errors == []:
                msg = jsonify({"message": "Saved to BigQuery and triggered agent pool successfully"})
                msg_log = f'{self.__class__.__name__}.{self.trigger_agent_pool.__name__} Saved to BigQuery and triggered agent pool successfully'

                self.publisher.publish_message(msg_log)

                return msg
            else:
                return jsonify({"message": f"Encountered errors: {errors}"})

        except Exception as e:
            error_msg = f'{self.__class__.__name__}.{self.trigger_agent_pool.__name__} encountered the Error: {str(e)}'
            self.logger.error(error_msg)
            self.publisher.publish_message(error_msg)
            raise Exception(e)

    def get_saved_setups(self):
        try:
            table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"
            if not self._table_exists(table_id):
                self._create_table(table_id)

            query = f"SELECT timestamp, data FROM `{table_id}`"
            results = self.bigquery_client.query(query).result()
            setups = [{"timestamp": row.timestamp, "data": [json.loads(item) for item in row.data.split('\n')]} for row
                      in results]
            return jsonify(setups)

        except Exception as e:
            error_msg = f'{self.__class__.__name__}.{self.get_saved_setups.__name__} encountered the Error: {str(e)}'
            self.logger.error(error_msg)
            self.publisher.publish_message(error_msg)
            raise Exception(e)

    def save_to_bigquery(self):
        try:
            data = request.json
            table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"
            if not self._table_exists(table_id):
                self._create_table(table_id)

            timestamp_str = datetime.datetime.utcnow().isoformat()
            data_as_jsonl = self._data_to_jsonl(data)

            rows_to_insert = [{"timestamp": timestamp_str, "data": data_as_jsonl}]
            errors = self.bigquery_client.insert_rows_json(table_id, rows_to_insert)
            if errors == []:
                return jsonify({"message": "Saved to BigQuery successfully"})
            else:
                return jsonify({"message": f"Encountered errors: {errors}"})

        except Exception as e:
            error_msg = f'{self.__class__.__name__}.{self.save_to_bigquery.__name__} encountered the Error: {str(e)}'
            self.logger.error(error_msg)
            self.publisher.publish_message(error_msg)
            raise Exception(e)

    def _table_exists(self, table_id):
        try:
            self.bigquery_client.get_table(table_id)
            return True
        except NotFound:
            return False

    def _create_table(self, table_id):
        try:
            schema = [
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("data", "STRING", mode="REQUIRED")
            ]
            table = bigquery.Table(table_id, schema=schema)
            table = self.bigquery_client.create_table(table)
            self.logger.info(f"Table {table_id} created successfully.")

        except Exception as e:
            error_msg = f'{self.__class__.__name__}.{self._create_table.__name__} encountered the Error: {str(e)}'
            self.logger.error(error_msg)
            self.publisher.publish_message(error_msg)
            raise Exception(e)

    def run(self):
        try:
            self.app.run(debug=True)
        except Exception as e:
            error_msg = f'{self.__class__.__name__}.{self.run.__name__} encountered the Error: {str(e)}'
            self.logger.error(error_msg)
            self.publisher.publish_message(error_msg)
            raise Exception(e)


if __name__ == '__main__':
    openai_api_key = os.getenv('OPEN_AI_KEY')
    open_ai_url = "https://api.openai.com/v1/chat/completions"
    app = AgentModelerApp(openai_api_key, open_ai_url)
    app.run()

# openai_api_key = os.getenv('OPEN_AI_KEY')
# open_ai_url = "https://api.openai.com/v1/chat/completions"
# app = AgentModelerApp(openai_api_key, open_ai_url)
#
# app.run()
