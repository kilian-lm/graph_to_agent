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

from Solver import Solver

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

class AgentModelerApp:

    def __init__(self, openai_api_key: str, url: str):
        self.app = Flask(__name__)
        self.app.secret_key = 'some_secret_key'
        self.setup_routes()
        self.openai_api_key = openai_api_key
        self.openai_base_url = url

        bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')
        bq_client_secrets_parsed = json.loads(bq_client_secrets)
        self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
        self.bigquery_client = bigquery.Client(credentials=self.bq_client_secrets,
                                               project=self.bq_client_secrets.project_id)
        self.project_id = self.bq_client_secrets.project_id

    def setup_routes(self):
        self.app.route('/')(self.index)
        self.app.route('/save_to_bigquery', methods=['POST'])(self.save_to_bigquery)
        self.app.route('/get_saved_setups', methods=['GET'])(self.get_saved_setups)
        self.app.route('/trigger_agent_pool', methods=['POST'])(self.trigger_agent_pool)

    def index(self):
        return render_template('index.html')

    def trigger_agent_pool(self):
        data = request.json
        problem_description = data.get('problemDescription', '')

        table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"
        if not self._table_exists(table_id):
            self._create_table(table_id)

        timestamp_str = datetime.datetime.utcnow().isoformat()

        rows_to_insert = [{
            u"timestamp": timestamp_str,
            u"data": json.dumps(data)
        }]

        errors = self.bigquery_client.insert_rows_json(table_id, rows_to_insert)
        if errors == []:
            return jsonify({"message": "Saved to BigQuery and triggered agent pool successfully"})
        else:
            return jsonify({"message": f"Encountered errors: {errors}"})

    def get_saved_setups(self):
        table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"
        if not self._table_exists(table_id):
            self._create_table(table_id)

        query = f"""
        SELECT timestamp, data
        FROM `{table_id}`
        """
        results = self.bigquery_client.query(query).result()
        setups = [{"timestamp": row.timestamp, "data": json.loads(row.data)} for row in results]
        return jsonify(setups)

    def save_to_bigquery(self):
        data = request.json
        table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"
        if not self._table_exists(table_id):
            self._create_table(table_id)

        timestamp_str = datetime.datetime.utcnow().isoformat()
        rows_to_insert = [{
            u"timestamp": timestamp_str,
            u"data": json.dumps(data)
        }]

        errors = self.bigquery_client.insert_rows_json(table_id, rows_to_insert)
        if errors == []:
            return jsonify({"message": "Saved to BigQuery successfully"})
        else:
            return jsonify({"message": f"Encountered errors: {errors}"})

    def _table_exists(self, table_id):
        try:
            self.bigquery_client.get_table(table_id)
            return True
        except Exception as e:  # Adjust with the specific exception type for a not found table
            return False

    def _create_table(self, table_id):
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("data", "STRING", mode="REQUIRED")
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
    openai_api_key = os.getenv('OPEN_AI_KEY')
    open_ai_url = "https://api.openai.com/v1/chat/completions"
    app = AgentModelerApp(openai_api_key, open_ai_url)
    app.run()

# class AgentModelerApp:
#
#     def __init__(self, openai_api_key: str, url: str):
#         self.app = Flask(__name__)
#         self.app.secret_key = 'some_secret_key'
#         self.setup_routes()
#         self.openai_api_key = openai_api_key
#         self.openai_base_url = url
#
#         bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')
#         bq_client_secrets_parsed = json.loads(bq_client_secrets)
#         self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
#         self.bigquery_client = bigquery.Client(credentials=self.bq_client_secrets,
#                                                project=self.bq_client_secrets.project_id)
#         self.project_id = self.bq_client_secrets.project_id
#
#     def setup_routes(self):
#         self.app.route('/')(self.index)
#         self.app.route('/save_to_session', methods=['POST'])(self.save_to_session)
#         self.app.route('/save_to_bigquery', methods=['POST'])(self.save_to_bigquery)
#         self.app.route('/get_saved_setups', methods=['GET'])(self.get_saved_setups)
#         self.app.route('/trigger_agent_pool', methods=['POST'])(self.trigger_agent_pool)
#
#     def index(self):
#         return render_template('index.html')
#
#     def save_to_session(self):
#         data = request.json
#         session['nodes_edges'] = data
#         return jsonify({"message": "Saved to session"})
#
#     def trigger_agent_pool(self):
#         data = request.json
#         problem_description = data.get('problemDescription', '')
#
#         # Save the problem setup to BigQuery
#         table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"
#         if not self._table_exists(table_id):
#             self._create_table(table_id)
#         timestamp_str = datetime.datetime.utcnow().isoformat()
#
#         # Instantiate Solver and trigger the agents
#         solver = self.create_solver_from_bigquery(table_id)
#         # Do something with the solver, for example:
#         # solution = solver.solve(problem_description)
#
#         # Here, add logic to get interactions and solutions from the solver
#         interactions = solver.get_interactions()
#         solutions = solver.get_solutions()
#
#         rows_to_insert = [
#             {
#                 u"timestamp": timestamp_str,
#                 u"data": json.dumps(data),
#                 u"interactions": json.dumps(interactions),
#                 u"solutions": json.dumps(solutions)
#             },
#         ]
#         errors = self.bigquery_client.insert_rows_json(table_id, rows_to_insert)
#
#         if errors == []:
#             return jsonify({"message": "Saved to BigQuery and triggered agent pool successfully"})
#         else:
#             return jsonify({"message": f"Encountered errors: {errors}"})
#
#     def get_saved_setups(self):
#         table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"
#
#         # Check if table exists, if not create it
#         if not self._table_exists(table_id):
#             self._create_table(table_id)
#
#         query = f"""
#         SELECT timestamp, data
#         FROM `{table_id}`
#         """
#         results = self.bigquery_client.query(query).result()
#         setups = [{"timestamp": row.timestamp, "data": json.loads(row.data)} for row in results]
#         return jsonify(setups)
#
#     def _table_exists(self, table_id):
#         """Check if a table exists."""
#         try:
#             self.bigquery_client.get_table(table_id)
#             return True
#         except Exception as e:  # Catch the specific exception for a not found table here
#             return False
#
#     def _create_table(self, table_id):
#         """Create a table with the necessary schema."""
#         schema = [
#             bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
#             bigquery.SchemaField("data", "STRING", mode="REQUIRED"),
#             bigquery.SchemaField("interactions", "STRING", mode="REPEATED"),
#             bigquery.SchemaField("solutions", "STRING", mode="REPEATED"),
#         ]
#         table = bigquery.Table(table_id, schema=schema)
#         try:
#             table = self.bigquery_client.create_table(table)
#             logging.info(f"Table {table_id} created successfully.")
#         except Exception as e:
#             logging.error(f"Error creating table {table_id}: {e}")
#
#     def save_to_bigquery(self, solver: Solver, problem_description: str):
#         """Saves Solver interactions to BigQuery."""
#         table_id = f"{self.project_id}.graph_to_agent.graph_to_agent_20231027"
#
#         # Check if table exists, if not, create it
#         if not self._table_exists(table_id):
#             self._create_table(table_id)
#
#         # Convert datetime objects to string
#         timestamp_str = datetime.utcnow().isoformat()
#
#         rows_to_insert = [{
#             u"timestamp": timestamp_str,
#             u"problem_description": problem_description,
#             u"agent_interactions": json.dumps(solver.agents),
#         }]
#
#         errors = self.bigquery_client.insert_rows_json(table_id, rows_to_insert)
#         if errors == []:
#             return jsonify({"message": "Saved to BigQuery successfully"})
#         else:
#             return jsonify({"message": f"Encountered errors: {errors}"})
#
#     def _create_solver_setup(self, data) -> dict:
#         """Process data to the right format for a Solver object."""
#         return {
#             'problem_description': data['problem_description'],
#             'agent_interactions': {entry['agent']: entry['messages'] for entry in data['agent_interactions']},
#             'solutions': data.get('solutions', {})
#         }
#
#     def create_solver_from_bigquery(self, table_id: str) -> Solver:
#         """Instantiate a Solver object from the most recent setup in BigQuery"""
#         query = f"""
#           SELECT data
#           FROM `{table_id}`
#           ORDER BY timestamp DESC
#           LIMIT 1
#           """
#         results = self.bigquery_client.query(query).result()
#         for row in results:
#             agents_setup = self._create_solver_setup(json.loads(row.data))
#             return Solver(openai_api_key="YOUR_OPENAI_API_KEY", url="YOUR_URL", agents=agents_setup)
#
#     def run(self):
#         self.app.run(debug=True)
#
#
# if __name__ == '__main__':
#     openai_api_key = os.getenv('OPEN_AI_KEY')
#     open_ai_url = "https://api.openai.com/v1/chat/completions"
#     app = AgentModelerApp(openai_api_key, open_ai_url)
#     app.run()
