from flask import Flask, render_template, request, jsonify, session
from google.cloud import bigquery
from google.oauth2.credentials import Credentials
import datetime
import os
import json
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
import logging


logging.basicConfig(level=logging.DEBUG)


load_dotenv()


class AgentModelerApp:

    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'some_secret_key'
        self.setup_routes()

        bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')
        bq_client_secrets_parsed = json.loads(bq_client_secrets)
        self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
        self.bigquery_client = bigquery.Client(credentials=self.bq_client_secrets,
                                               project=self.bq_client_secrets.project_id)
        self.project_id = self.bq_client_secrets.project_id

    def setup_routes(self):
        self.app.route('/')(self.index)
        self.app.route('/save_to_session', methods=['POST'])(self.save_to_session)
        self.app.route('/save_to_bigquery', methods=['POST'])(self.save_to_bigquery)
        self.app.route('/get_saved_setups', methods=['GET'])(self.get_saved_setups)

    def index(self):
        return render_template('index.html')

    def save_to_session(self):
        data = request.json
        session['nodes_edges'] = data
        return jsonify({"message": "Saved to session"})

    def save_to_bigquery(self):
        data = request.json
        table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"

        # Check if table exists, if not, create it
        if not self._table_exists(table_id):
            self._create_table(table_id)

        # Convert datetime objects to string
        timestamp_str = datetime.datetime.utcnow().isoformat()

        rows_to_insert = [
            {
                u"timestamp": timestamp_str,
                u"data": json.dumps(data),
            },
        ]

        errors = self.bigquery_client.insert_rows_json(table_id, rows_to_insert)
        if errors == []:
            return jsonify({"message": "Saved to BigQuery successfully"})
        else:
            return jsonify({"message": f"Encountered errors: {errors}"})

    def get_saved_setups(self):
        table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"

        # Check if table exists, if not create it
        if not self._table_exists(table_id):
            self._create_table(table_id)

        query = f"""
        SELECT timestamp, data
        FROM `{table_id}`
        """
        results = self.bigquery_client.query(query).result()
        setups = [{"timestamp": row.timestamp, "data": json.loads(row.data)} for row in results]
        return jsonify(setups)

    def _table_exists(self, table_id):
        """Check if a table exists."""
        try:
            self.bigquery_client.get_table(table_id)
            return True
        except Exception as e:  # Catch the specific exception for a not found table here
            return False

    def _create_table(self, table_id):
        """Create a table with the necessary schema."""
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("data", "STRING", mode="REQUIRED"),
        ]
        table = bigquery.Table(table_id, schema=schema)
        try:
            table = self.bigquery_client.create_table(table)
            logging.info(f"Table {table_id} created successfully.")
        except Exception as e:
            logging.error(f"Error creating table {table_id}: {e}")

    def run(self):
        self.app.run(debug=True)


if __name__ == '__main__':
    app = AgentModelerApp()
    app.run()
