# ToDo :: 
# 1. Get tables
# 2. Follow rules
## Match either 'user', 'system'
## After matching, bring it into 'role'-hierarchy-json-logic
## All != 'user', 'system' -> 'content'



"""
https://chat.openai.com/share/1adc25f3-e475-460d-b713-cb0093e65690
I see, you're looking to incorporate the responses of a sequence of agents, each building upon the previous one's knowledge, within a system that primarily operates through a `user -> content -> system` transition flow.

Given this structure, we could consider each agent's response as a form of `content` that gets passed along to the next `system` call. In this way, the `agent_response` is essentially becoming a node within this transition graph. Here’s a conceptual extension of the current transition schema:

1. **Initial Transition** (unchanged):
   - `user`: Represents the user's input/query.
   - `content`: Represents the content created by the system in response to the user.
   - `system`: Represents the system's processing of the content.

2. **Extended Transition** (incorporating agents):
   - After `system`, introduce a `agent_response` node.
   - `agent_response`: Represents the processed content by an agent, which is effectively a part of the content node with added information.
   - `user (variable)`: Represents the user with the placeholder for the agent's response. This is where the transition schema now begins to loop back, incorporating the agent's input.

Here's how you could model this within the constraints of your transition system:

```python
valid_transitions = {
    'user': 'content',
    'content': 'system',
    'system': 'agent_response',
    'agent_response': 'user (variable)'
}

def process_agents_sequence(agents_data):
    responses = []
    agent_content = None

    for agent_name, agent_info in agents_data.items():
        # The system processes the content
        system_content = process_system(agent_content)

        # The agent provides a response based on the system content
        agent_content = {
            "role": "agent: " + agent_name,
            "content": system_content + " plus agent's knowledge"
        }

        # This agent's content will be the input for the next system call
        responses.append(agent_content)

        # Prepare the user (variable) for the next iteration
        user_variable = prepare_user_variable(agent_content)

        # Simulate the loop back to 'content' node with the updated user_variable
        agent_content = user_variable

    return responses

def process_system(previous_content):
    # This function would be where the system processes the 'content' node
    # For this example, it's a placeholder function that just appends additional text
    return previous_content['content'] + " after system processing" if previous_content else "initial system content"

def prepare_user_variable(agent_content):
    # Prepare the user (variable) to incorporate the agent's response
    return {
        "role": "user (variable)",
        "content": agent_content['content']
    }

# Example usage
agents_data = {
    "Agent 1": {"info": "Agent 1's specific data"},
    "Agent 2": {"info": "Agent 2's specific data"},
    # ... add more agents as necessary
}

# Begin the sequence of agent processing
agent_responses = process_agents_sequence(agents_data)
```

In this setup, each agent's response is fed back into the system as a new `user (variable)` content, which then goes through the `system` again before reaching the next agent. This allows for each agent to build upon the previous agent's knowledge while still operating within the `user -> content -> system -> agent_response -> user (variable)` loop.


"""
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

load_dotenv()

logging.basicConfig(level=logging.INFO)  # You can change the level as needed.
logger = logging.getLogger(__name__)




class TranslatorGraphToGpt:
    def __init__(self, dataset_id):
        self.dataset_id = dataset_id
        bq_client_secrets = os.getenv('BQ_CLIENT_SECRETS')

        try:
            bq_client_secrets_parsed = json.loads(bq_client_secrets)
            self.bq_client_secrets = Credentials.from_service_account_info(bq_client_secrets_parsed)
            self.bigquery_client = bigquery.Client(credentials=self.bq_client_secrets,
                                                   project=self.bq_client_secrets.project_id)
            logger.info("BigQuery client successfully initialized.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse BQ_CLIENT_SECRETS environment variable: {e}")
            raise
        except Exception as e:
            logger.error(f"An error occurred while initializing the BigQuery client: {e}")
            raise

    def load_graph_data_by_id(self, graph_id):
        nodes_table_ref = self.bigquery_client.dataset(self.dataset_id).table("nodes_table")
        edges_table_ref = self.bigquery_client.dataset(self.dataset_id).table("edges_table")

        # Fetch nodes for given graph_id
        nodes_query = f"SELECT * FROM `{self.dataset_id}.nodes_table` WHERE graph_id = '{graph_id}'"
        nodes_query_job = self.bigquery_client.query(nodes_query)
        nodes_results = nodes_query_job.result()
        nodes = [{"id": row['id'], "label": row['label']} for row in nodes_results]

        logger.info(f"nodes loaded by graph id {nodes} already exists.")

        # Fetch edges for given graph_id
        edges_query = f"SELECT * FROM `{self.dataset_id}.edges_table` WHERE graph_id = '{graph_id}'"
        edges_query_job = self.bigquery_client.query(edges_query)
        edges_results = edges_query_job.result()
        edges = [{"from": row['from'], "to": row['to']} for row in edges_results]

        return {"nodes": nodes, "edges": edges}



transl = TranslatorGraphToGpt('graph_to_agent')

transl.load_graph_data_by_id('20231102113520')

import json

# Load the graph data from a JSON file
# with open('logics/eg_vis_graph_to_gpt.jsonl', 'r') as file:
#     data = json.load(file)

# Path to your .jsonl file
file_path = 'logics/eg_vis_graph_to_gpt.jsonl'

# Initialize lists to hold your nodes and edges
nodes = []
edges = []

# Open the file and process it line by line
with open(file_path, 'r') as file:
    for line in file:
        # Parse the JSON object from each line
        json_obj = json.loads(line)

        # Depending on the structure of your JSON object, append it to the appropriate list
        if 'label' in json_obj:
            # This is a node
            nodes.append(json_obj)
        elif 'from' in json_obj and 'to' in json_obj:
            # This is an edge
            edges.append(json_obj)

# Assuming the JSON data structure is a list where the first element contains nodes and the second contains edges
nodes = data[0]
edges = data[1]


# Function to check if a label is 'user' or 'system'
def is_user_or_system(label):
    return label in ['user', 'system']

# Build a mapping of node IDs to labels
node_mapping = {node['id']: node['label'] for node in nodes}

# Initialize the data structure
data = {
    "model": "gpt-4",
    "messages": []
}

# Track processed content nodes to avoid duplication
processed_contents = set()

# Iterate through edges to build messages
for edge in edges:
    from_node = node_mapping[edge['from']]
    to_node_id = edge['to']

    # Process only content nodes and ensure they are only processed once
    if not is_user_or_system(from_node) and to_node_id not in processed_contents:
        # Find the connected user or system node
        connected_role = next((node_mapping[e['from']] for e in edges if e['to'] == to_node_id and is_user_or_system(node_mapping[e['from']])), None)
        if connected_role:
            # Add the message to the data structure
            content = from_node
            data['messages'].append({
                "role": connected_role,
                "content": content
            })
            processed_contents.add(to_node_id)

# Serialize data to json
json_data = json.dumps(data, indent=4)
print(json_data)