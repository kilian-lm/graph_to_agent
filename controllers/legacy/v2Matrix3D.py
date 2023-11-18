from typing import List, Dict
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
from logger.CustomLogger import CustomLogger
import inspect
import re




json_graph_data = """{
  "nodes": [
    {
      "id": "07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! As I'm an expert in the .puml syntax i will correct it"
    },
    {
      "id": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "The following is a .puml content generated by an agent. Please critically review it and correct any mistakes, especially ensuring it strictly adheres to .puml syntax and does not contain any elements from other diagramming languages like Mermaid"
    },
    {
      "id": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    },
    {
      "id": "eac6de73-9726-43b7-9441-f8e319a972e6",
      "label": "@variable_1_2"
    },
    {
      "id": "copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
      "label": "sequenceDiagramAlice->>John: Hello John, how are you?John-->>Alice: Great!Alice-)John: See you later!"
    },
    {
      "id": "copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! As I'm an expert in the .puml syntax i will correct it"
    },
    {
      "id": "copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "The following is a .puml content generated by an agent. Please critically review it and correct any mistakes, especially ensuring it strictly adheres to .puml syntax and does not contain any elements from other diagramming languages like Mermaid"
    },
    {
      "id": "copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    },
    {
      "id": "copied-1699889663524-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    },
    {
      "id": "copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! , I'm agent-'Deductive Reasoning', solving problems like you just described. Please provide the problem-space for me to navigate it best as possible..."
    },
    {
      "id": "copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "You're agent-'Deductive Reasoning'. You're one agent out of 7 who try to model problem-spaces and suggest solutions based on logical reasoning, similar to the detectives of The Poisoned Chocolates Case. Your strength lies in deriving specific conclusions from general hypotheses. Utilize schemas like Modus Ponens, Modus Tollens, Hypothetical Syllogism, and Disjunctive Syllogism., in order to solve problems, you use one of the following schemas ['Modus Ponens', 'Modus Tollens', 'Hypothetical Syllogism', 'Disjunctive Syllogism']"
    },
    {
      "id": "copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
      "label": "How would you model following problem-space?: There was a attack of the Palestinien sided group Hamas on Israel. Now Israel is bombing Gaza with heavy civiliens casualties. There is a total 'cleaning' of the Hamas in Gaza planned by Isralien-Army. There is a high danger that the whole region will fall into war.."
    },
    {
      "id": "copied-1699890186553-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! I will review following .mmd"
    },
    {
      "id": "copied-1699890186553-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "You're an expert in mermeid .mmd and you nedd to review following .mmd"
    },
    {
      "id": "copied-1699890186553-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "copied-1699890186553-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "copied-1699890186553-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    },
    {
      "id": "234ec0c2-3d02-4ef5-9fb1-7adaeb58a1b6",
      "x": 1626.674810293892,
      "y": -632.9703327332509,
      "label": "@varibale_1_1"
    },
    {
      "id": "copied-1699891124900-234ec0c2-3d02-4ef5-9fb1-7adaeb58a1b6",
      "x": 1626.674810293892,
      "y": -632.9703327332509,
      "label": "@varibale_1"
    },
    {
      "id": "copied-1699891124900-copied-1699889663524-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "label": "user"
    },
    {
      "id": "copied-1699891124900-copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "label": "Understood! , I'm agent-'Inductive Reasoning', solving problems like you just described. Please provide the problem-space for me to navigate it best as possible..."
    },
    {
      "id": "copied-1699891124900-copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "label": "You're agent-'Inductive Reasoning'. You're one agent out of 7 who try to model problem-spaces and suggest solutions based on logical reasoning, similar to the detectives of The Poisoned Chocolates Case. Your expertise is in drawing general conclusions from specific observations. Harness schemas such as Simple Induction, Inverse Induction, Causal Inference, and Statistical Generalization., in order to solve problems, you use one of the following schemas ['Simple Induction', 'Inverse Induction', 'Causal Inference', 'Statistical Generalization']"
    },
    {
      "id": "copied-1699891124900-copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "label": "system"
    },
    {
      "id": "copied-1699891124900-copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "label": "user"
    },
    {
      "id": "copied-1699891124900-copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
      "label": "How would you model following problem-space?: There was a attack of the Palestinien sided group Hamas on Israel. Now Israel is bombing Gaza with heavy civiliens casualties. There is a total 'cleaning' of the Hamas in Gaza planned by Isralien-Army. There is a high danger that the whole region will fall into war.."
    }
  ],
  "edges": [
    {
      "from": "07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "67194bdc-f1f3-417f-9778-4d163c8b82d1",
      "to": "757e7439-08f8-4cea-afac-c25b01167d32"
    },
    {
      "from": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
      "to": "2e419e7e-a540-4c9a-af4e-5110e54fad96"
    },
    {
      "from": "2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "33312b2e-b683-4489-b471-e2d1ca03d21a",
      "to": "07537a68-1c7e-4edb-a72f-2d82015c490f"
    },
    {
      "from": "757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "f5b47e5e-4121-44a3-8b29-97bfe2069148",
      "to": "eac6de73-9726-43b7-9441-f8e319a972e6"
    },
    {
      "from": "c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "id": "f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
      "to": "1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
    },
    {
      "from": "copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "copied-1699797991293-f5b47e5e-4121-44a3-8b29-97bfe2069148",
      "to": "copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6"
    },
    {
      "from": "copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "copied-1699797991293-67194bdc-f1f3-417f-9778-4d163c8b82d1",
      "to": "copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32"
    },
    {
      "from": "copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "copied-1699797991293-33312b2e-b683-4489-b471-e2d1ca03d21a",
      "to": "copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f"
    },
    {
      "from": "copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "copied-1699797991293-1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
      "to": "copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96"
    },
    {
      "from": "copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "id": "copied-1699797991293-f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
      "to": "copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
    },
    {
      "from": "copied-1699889663524-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "id": "copied-1699889663524-copied-1699797991293-f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
      "to": "copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
    },
    {
      "from": "copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "copied-1699889663524-copied-1699797991293-67194bdc-f1f3-417f-9778-4d163c8b82d1",
      "to": "copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32"
    },
    {
      "from": "copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "copied-1699889663524-copied-1699797991293-33312b2e-b683-4489-b471-e2d1ca03d21a",
      "to": "copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f"
    },
    {
      "from": "copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "copied-1699889663524-copied-1699797991293-1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
      "to": "copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96"
    },
    {
      "from": "copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "copied-1699890186553-copied-1699889663524-copied-1699797991293-f5b47e5e-4121-44a3-8b29-97bfe2069148",
      "to": "copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6"
    },
    {
      "from": "copied-1699890186553-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "copied-1699890186553-copied-1699797991293-67194bdc-f1f3-417f-9778-4d163c8b82d1",
      "to": "copied-1699890186553-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32"
    },
    {
      "from": "copied-1699890186553-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "copied-1699890186553-copied-1699797991293-33312b2e-b683-4489-b471-e2d1ca03d21a",
      "to": "copied-1699890186553-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f"
    },
    {
      "from": "copied-1699890186553-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "copied-1699890186553-copied-1699797991293-1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
      "to": "copied-1699890186553-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96"
    },
    {
      "from": "copied-1699890186553-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "id": "copied-1699890186553-copied-1699797991293-f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
      "to": "copied-1699890186553-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
    },
    {
      "from": "copied-1699890186553-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "copied-1699890186553-copied-1699797991293-f5b47e5e-4121-44a3-8b29-97bfe2069148",
      "to": "copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6"
    },
    {
      "from": "234ec0c2-3d02-4ef5-9fb1-7adaeb58a1b6",
      "to": "copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
      "id": "218594c0-41f7-4e0b-bea6-de7aa2349017"
    },
    {
      "from": "copied-1699891124900-234ec0c2-3d02-4ef5-9fb1-7adaeb58a1b6",
      "to": "copied-1699891124900-copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6",
      "id": "copied-1699891124900-218594c0-41f7-4e0b-bea6-de7aa2349017"
    },
    {
      "from": "copied-1699891124900-copied-1699889663524-copied-1699797991293-c7d1c0a4-6365-44d6-be0c-bd3fc5436b85",
      "id": "copied-1699891124900-copied-1699889663524-copied-1699797991293-f4e2015e-e7f1-4e03-b3c6-ee82986533ca",
      "to": "copied-1699891124900-copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0"
    },
    {
      "from": "copied-1699891124900-copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f",
      "id": "copied-1699891124900-copied-1699889663524-copied-1699797991293-67194bdc-f1f3-417f-9778-4d163c8b82d1",
      "to": "copied-1699891124900-copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32"
    },
    {
      "from": "copied-1699891124900-copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96",
      "id": "copied-1699891124900-copied-1699889663524-copied-1699797991293-33312b2e-b683-4489-b471-e2d1ca03d21a",
      "to": "copied-1699891124900-copied-1699889663524-copied-1699797991293-07537a68-1c7e-4edb-a72f-2d82015c490f"
    },
    {
      "from": "copied-1699891124900-copied-1699889663524-copied-1699797991293-1cc45118-72ee-4efe-95d8-06e8c02fb4c0",
      "id": "copied-1699891124900-copied-1699889663524-copied-1699797991293-1329a8be-e4e2-42fd-bdb6-2057f9c320d3",
      "to": "copied-1699891124900-copied-1699889663524-copied-1699797991293-2e419e7e-a540-4c9a-af4e-5110e54fad96"
    },
    {
      "from": "copied-1699891124900-copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "id": "copied-1699891124900-copied-1699890186553-copied-1699889663524-copied-1699797991293-f5b47e5e-4121-44a3-8b29-97bfe2069148",
      "to": "copied-1699891124900-copied-1699890186553-copied-1699889663524-copied-1699797991293-eac6de73-9726-43b7-9441-f8e319a972e6"
    },
    {
      "from": "copied-1699891124900-copied-1699889663524-copied-1699797991293-757e7439-08f8-4cea-afac-c25b01167d32",
      "to": "234ec0c2-3d02-4ef5-9fb1-7adaeb58a1b6",
      "id": "b81f1bc6-e4c9-4082-8078-f1b64eac0597"
    }
  ]
}"""


graph_data = json.loads(json_graph_data)
class CubeMatrix:
    def __init__(self, graph_data: Dict[str, List[Dict[str, str]]]):
        self.graph_data = graph_data
        self.matrix = None
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        print(timestamp)
        self.log_file = f'{timestamp}_blueprint_designer.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)


    def create_matrix(self, graph_data: Dict[str, List[Dict[str, str]]]):
        # Create the binary-coded plane
        node_ids = [node['id'] for node in self.graph_data['nodes']]
        self.matrix = [[int(node_id in graph_data['nodes'][i].get('edges', [])) for node_id in node_ids]
                       for i in range(len(node_ids))]

        # Add subsequent layers with string data
        for layer in range(len(node_ids)):
            for i in range(len(node_ids)):
                self.matrix[layer][i] = [self.graph_data['nodes'][i]['label']]

        return self.matrix

cbm = CubeMatrix(graph_data)

cbm.create_matrix(graph_data)
from typing import List, Dict


# class CubeMatrix:
#     def __init__(self, graph_data: Dict[str, List[Dict[str, str]]]):
#         self.graph_data = graph_data
#         self.matrix = None
#
#     def create_matrix(self) -> List[List[List[str]]]:
#         # Create the binary-coded plane
#         node_ids = [node['id'] for node in self.graph_data['nodes']]
#         self.matrix = [[int(node_id in graph_data['nodes'][i].get('edges', [])) for node_id in node_ids]
#                        for i in range(len(node_ids))]
#
#         # Add subsequent layers with string data
#         for layer in range(1, len(node_ids)):
#             for i in range(len(node_ids)):
#                 if self.check_pattern(node_ids[i], layer):
#                     self.matrix[layer][i].append(self.graph_data['nodes'][i]['label'])
#
#         return self.matrix
#
#     def check_pattern(self, node_id: str, layer: int) -> bool:
#         pattern = ["user", "system", "user"]
#         for i in range(layer):
#             connecting_node_ids = [edge_id for edge_id in self.graph_data['nodes'][i].get('edges', []) if
#                                    edge_id != node_id]
#             # Check if the connecting nodes have the required labels in the specified order
#             if len(connecting_node_ids) == len(pattern):
#                 labels = [self.graph_data['nodes'][j]['label'] for j in range(len(node_ids)) if
#                           node_ids[j] in connecting_node_ids]
#                 if labels == pattern:
#                     return True
#         return False