import os
import json
from typing import Optional
import requests
from dotenv import load_dotenv
import logging

import json
import requests
import logging
from datetime import datetime
import datetime
import json

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from google.cloud.exceptions import NotFound

load_dotenv()

from google.cloud import bigquery
from google.oauth2.credentials import Credentials
import datetime

from app.LoggerPublisher.MainPublisher import MainPublisher
from app.LoggerPublisher.MainLogger import MainLogger

from google.oauth2.service_account import Credentials

class Solver:
    def __init__(self, openai_api_key: str, url: str, agents=None):
        print("__init__")
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
        self.table_id = f"enter-universes.graph_to_agent.graph_to_agent_{datetime.datetime.now().strftime('%Y%m%d')}"

        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.openai_api_key}'
        }

        if agents is None:
            self.agents = {
                "Deductive Reasoning": {
                    "schema": ["Modus Ponens", "Modus Tollens", "Hypothetical Syllogism", "Disjunctive Syllogism"],
                    "briefing": "Your strength lies in deriving specific conclusions from general hypotheses. Utilize schemas like Modus Ponens, Modus Tollens, Hypothetical Syllogism, and Disjunctive Syllogism."
                },
                "Inductive Reasoning": {
                    "schema": ["Simple Induction", "Inverse Induction", "Causal Inference",
                               "Statistical Generalization"],
                    "briefing": "Your expertise is in drawing general conclusions from specific observations. Harness schemas such as Simple Induction, Inverse Induction, Causal Inference, and Statistical Generalization."
                },
                "Abductive Reasoning": {
                    "schema": ["Inference to the Best Explanation", "Eliminative Induction"],
                    "briefing": "Your capability shines when discerning the most plausible explanation from a set of observations. Employ schemas like Inference to the Best Explanation and Eliminative Induction."
                },
                "Analogical Reasoning": {
                    "schema": ["Positive Analogy", "Negative Analogy", "Partial Analogy"],
                    "briefing": "Your forte is comparing similar situations and deriving conclusions from parallels. Lean on schemas like Positive Analogy, Negative Analogy, and Partial Analogy."
                },
                "Causal Reasoning": {
                    "schema": ["Cause-to-Effect", "Effect-to-Cause", "Common-Cause Reasoning"],
                    "briefing": "You excel in identifying cause-and-effect relationships. Use schemas such as Cause-to-Effect, Effect-to-Cause, and Common-Cause Reasoning."
                },
                "Counterfactual Reasoning": {
                    "schema": ["Conditional Counterfactual", "Causal Counterfactual"],
                    "briefing": "You thrive on imagining alternate scenarios and outcomes. Draw from schemas like Conditional Counterfactual and Causal Counterfactual."
                },
                "Probabilistic Reasoning": {
                    "schema": ["Bayesian Updating", "Statistical Reasoning", "Probability Tree Analysis"],
                    "briefing": "Your domain is estimating likelihoods and outcomes. Engage with schemas such as Bayesian Updating, Statistical Reasoning, and Probability Tree Analysis."
                }
            }
        else:
            self.agents = agents

    def model_problem_spaces(self, problem_description: str) -> str:
        print("model_problem_spaces")
        responses = []
        previous_agent_reasoning = []

        # Create logs dictionary to store interactions
        logs = {
            "problem_description": problem_description,
            "agent_interactions": []
        }

        logging.info("Starting to process agents' interactions...")
        print("Start")
        for agent_name, agent_info in self.agents.items():
            logging.info(f"Processing agent '{agent_name}'...")
            print(f"Processing agent '{agent_name}'...")
            messages = [
                {
                    "role": "user",
                    "content": f"You're agent-'{agent_name}'. You're one agent out of {len(self.agents)} who try to model problem-spaces and suggest solutions based on logical reasoning, similar to the detectives of The Poisoned Chocolates Case. {agent_info['briefing']}, in order to solve problems, you use one of the following schemas {agent_info['schema']}"
                },
                {
                    "role": "system",
                    "content": f"Understood! , I'm agent-'{agent_name}', solving problems like you just described. Please provide the problem-space for me to navigate it best as possible..."
                }
            ]

            # Review previous agents' reasoning if this isn't the first agent
            if previous_agent_reasoning:
                review_messages = [
                    f"Agent {reasoning['role'].split(':')[1].strip()}'s reasoning was: {reasoning['content']}. How do you view this from your perspective?"
                    for reasoning in previous_agent_reasoning]
                messages.extend({"role": "user", "content": review} for review in review_messages)

            messages.append({
                "role": "user",
                "content": f"How would you model the following problem-space?: {problem_description}."
            })

            data = {"model": "gpt-4", "messages": messages}
            logging.info(f"Sending the data for agent '{agent_name}' to the model for processing...")

            response = requests.post(self.openai_base_url, headers=self.headers, json=data)
            agent_response = response.json()["choices"][0]["message"]["content"]
            responses.append({"role": "agent: " + agent_name, "content": agent_response})

            logging.info(f"Received response from agent '{agent_name}': {agent_response}")

            # Store the agent's reasoning for the next agent
            previous_agent_reasoning.insert(0, {"role": "agent: " + agent_name, "content": agent_response})

            # Append this interaction to logs
            interaction = {
                "agent": agent_name,
                "messages": messages + [{"role": "agent: " + agent_name, "content": agent_response}]
            }
            logs["agent_interactions"].append(interaction)

            logging.info(f"Updated logs with agent '{agent_name}' interaction.")

        # Serialize logs dictionary to a .json file with a timestamp in its name
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"agent_interactions_{timestamp}.json"
        logging.info(f"Serializing logs to '{filename}'...")
        with open(filename, "w") as f:
            json.dump(logs, f, indent=4)

        nodes, edges = self.convert_logs_to_graph_data(logs)
        graph_data = {"nodes": nodes, "edges": edges}
        filename_graph = f"agent_graph_data_{timestamp}.json"
        logging.info(f"Serializing graph data to '{filename_graph}'...")
        with open(filename_graph, "w") as f:
            json.dump(graph_data, f, indent=4)

        logging.info("Processing complete. Check the output file for full logs.")
        # self.create_table_if_not_exists()
        # self.save_to_bigquery(logs)

        return responses

    def convert_logs_to_graph_data(self, logs):
        nodes = []
        edges = []

        for interaction in logs["agent_interactions"]:
            agent_name = interaction["agent"]

            # Create node for the agent
            nodes.append({"id": agent_name, "label": agent_name})

            # Check the messages for interactions with other agents
            for message in interaction["messages"]:
                role = message["role"]
                if role.startswith("agent:"):
                    mentioned_agents = [msg.split(':')[1].strip() for msg in message["content"].split("Agent") if
                                        "Agent" in msg]
                    for mentioned_agent in mentioned_agents:
                        edges.append({"from": agent_name, "to": mentioned_agent})

        return nodes, edges


    def define_table_schema(self):
        # Define schema
        schema = [
            bigquery.SchemaField("timestamp", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("problem_description", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("agent_interactions", "RECORD", mode="REPEATED", fields=[
                bigquery.SchemaField("agent", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("messages", "RECORD", mode="REPEATED", fields=[
                    bigquery.SchemaField("role", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("content", "STRING", mode="REQUIRED")
                ])
            ])
        ]
        return schema

    def create_table_if_not_exists(self):
        dataset_ref = self.bigquery_client.dataset("enter-universes")
        table_ref = dataset_ref.table(f"graph_to_agent.graph_to_agent_{datetime.datetime.now().strftime('%Y%m%d')}")

        try:
            # This will raise a NotFound exception if the table doesn't exist.
            self.bigquery_client.get_table(table_ref)
            logging.info("Table already exists.")
        except NotFound:
            logging.info("Table does not exist. Creating...")
            schema = self.define_table_schema()
            table = bigquery.Table(table_ref, schema=schema)
            table = self.bigquery_client.create_table(table)
            logging.info(f"Created table {table.full_table_id}")


    def save_to_bigquery(self, logs):
        # Prepare the rows to be inserted
        rows_to_insert = [{
            "timestamp": datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),
            "problem_description": logs["problem_description"],
            "agent_interactions": logs["agent_interactions"]
        }]

        # Insert rows to BQ
        errors = self.bigquery_client.insert_rows_json(self.table_id, rows_to_insert)
        if errors:
            logging.error(f"Failed to insert rows into BigQuery: {errors}")
        else:
            logging.info("Successfully saved to BigQuery")

    # def save_to_bigquery(self, client: bigquery.Client, table_id: str):
    #     """Save the agent's interactions to BigQuery"""
    #
    #     print("save_to_bigquery")
    #
    #     timestamp_str = datetime.datetime.utcnow().isoformat()
    #
    #     rows_to_insert = [{
    #         "timestamp": timestamp_str,
    #         "data": json.dumps(self.agents),
    #     }]
    #
    #     errors = client.insert_rows_json(table_id, rows_to_insert)
    #     if errors:
    #         logging.error(f"Encountered errors while saving to BigQuery: {errors}")
    #     else:
    #         logging.info(f"Saved to BigQuery successfully.")

openai_api_key = os.getenv('OPEN_AI_KEY')
open_ai_url = "https://api.openai.com/v1/chat/completions"
bot = Solver(openai_api_key, open_ai_url)

problem_space = "There was a attack of the Palestinien sided group Hamas on Israel. Now Israel is bombing Gaza with heavy civiliens casualties. There is a total 'cleaning' of the Hamas in Gaza planned by Isralien-Army. There is a high danger that the whole region will fall into war."

bot.model_problem_spaces(problem_space)
