from typing import List, Dict


class CubeMatrix:
    def __init__(self, graph_data: Dict[str, List[Dict[str, str]]]):
        self.graph_data = graph_data
        self.matrix = None

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