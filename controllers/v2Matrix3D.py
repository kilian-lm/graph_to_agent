from typing import List, Dict


class CubeMatrix:
    def __init__(self, graph_data: Dict[str, List[Dict[str, str]]]):
        self.graph_data = graph_data
        self.matrix = None

    def create_matrix(self) -> List[List[List[str]]]:
        # Create the binary-coded plane
        node_ids = [node['id'] for node in self.graph_data['nodes']]
        self.matrix = [[int(node_id in graph_data['nodes'][i].get('edges', [])) for node_id in node_ids]
                       for i in range(len(node_ids))]

        # Add subsequent layers with string data
        for layer in range(len(node_ids)):
            for i in range(len(node_ids)):
                self.matrix[layer][i] = [self.graph_data['nodes'][i]['label']]

        return self.matrix