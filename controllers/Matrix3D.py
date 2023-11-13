class Matrix3D:
    def __init__(self, graph_data):
        self.graph_data = graph_data
        self.patterns = self.find_patterns()

    def create_binary_layer(self):
        # Create a binary layer based on node connections
        nodes = self.graph_data["nodes"]
        edges = self.graph_data["edges"]
        binary_layer = {}
        for node in nodes:
            binary_layer[node["id"]] = {}
            for other_node in nodes:
                if any(edge["from"] == node["id"] and edge["to"] == other_node["id"] for edge in edges):
                    binary_layer[node["id"]][other_node["id"]] = 1
                else:
                    binary_layer[node["id"]][other_node["id"]] = 0
        return binary_layer

    def create_label_layer(self):
        # Create a label layer based on node labels
        nodes = self.graph_data["nodes"]
        label_layer = {}
        for node in nodes:
            label_layer[node["id"]] = node["label"]
        return label_layer

    def find_patterns(self):
        # Find hierarchical patterns in the 3D matrix
        patterns = []
        nodes = self.graph_data["nodes"]

        def is_valid_pattern(pattern):
            # Check if a pattern is valid (e.g., "user", "system", "user")
            if len(pattern) != 6:
                return False
            return (
                    pattern[0].startswith("user") and
                    pattern[2].startswith("system") and
                    pattern[4].startswith("user")
            )

        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if self.create_binary_layer[nodes[i]["id"]][nodes[j]["id"]] == 1:
                    for k in range(j + 1, len(nodes)):
                        if (
                                self.create_binary_layer[nodes[j]["id"]][nodes[k]["id"]] == 1
                                and self.create_binary_layer[nodes[i]["id"]][nodes[k]["id"]] == 1
                        ):
                            pattern = (
                                nodes[i]["label"],
                                nodes[j]["label"],
                                nodes[j]["label"],  # some text
                                nodes[k]["label"],
                                nodes[k]["label"],  # some text
                                nodes[i]["label"],
                            )
                            if is_valid_pattern(pattern):
                                patterns.append(pattern)
        return patterns

    def get_patterns(self):
        # Return the found patterns
        return self.patterns
