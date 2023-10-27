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

load_dotenv()

from google.cloud import bigquery
from google.oauth2.credentials import Credentials


class Solver:
    def __init__(self, openai_api_key: str, url: str, agents=None):
        self.openai_api_key = openai_api_key
        self.openai_base_url = url
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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"agent_interactions_{timestamp}.json"
        logging.info(f"Serializing logs to '{filename}'...")
        with open(filename, "w") as f:
            json.dump(logs, f, indent=4)

        logging.info("Processing complete. Check the output file for full logs.")

        return responses

    def save_to_bigquery(self, client: bigquery.Client, table_id: str):
        """Save the agent's interactions to BigQuery"""
        timestamp_str = datetime.datetime.utcnow().isoformat()

        rows_to_insert = [{
            "timestamp": timestamp_str,
            "data": json.dumps(self.agents),
        }]

        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            logging.error(f"Encountered errors while saving to BigQuery: {errors}")
        else:
            logging.info(f"Saved to BigQuery successfully.")


# openai_api_key = os.getenv('OPEN_AI_KEY')
# open_ai_url = "https://api.openai.com/v1/chat/completions"
# bot = Solver(openai_api_key, open_ai_url)
#
# problem_space = "There was a attack of the Palestinien sided group Hamas on Israel. Now Israel is bombing Gaza with heavy civiliens casualties. There is a total 'cleaning' of the Hamas in Gaza planned by Isralien-Army. There is a high danger that the whole region will fall into war."
#
# bot.model_problem_spaces(problem_space)
