class VarIdentificationProcess:
    def __init__(self, graph, num_steps):
        self.graph = graph
        self.num_steps = num_steps

    def classify_gpt_calls(self):
        matched = []
        unmatched = []
        user_nodes = self.get_user_nodes()
        variable_suffix_nodes = self.get_variable_suffix_nodes()

        for start_node in user_nodes:
            for path in self.explore_paths(start_node):
                gpt_call = self.check_gpt_call(path)
                if gpt_call:
                    if any(node in variable_suffix_nodes for node in path):
                        matched.append(gpt_call)
                    else:
                        unmatched.append(gpt_call)

        return matched, unmatched

    def get_user_nodes(self):
        return [node for node, attrs in self.graph.nodes(data=True) if attrs['label'] == 'user']

    def get_variable_suffix_nodes(self):
        return [node for node in self.graph.nodes() if self.is_variable_node(self.graph.nodes[node]['label'])]

    def is_variable_node(self, label):
        return label.startswith('@')

    def explore_paths(self, start_node):
        paths = []
        self.dfs(start_node, [], paths)
        return paths

    def dfs(self, node, path, paths):
        if len(path) > self.num_steps or node in path:
            return
        path.append(node)
        if len(path) == self.num_steps + 1:
            paths.append(path.copy())
        else:
            for neighbor in self.graph.neighbors(node):
                self.dfs(neighbor, path, paths)
        path.pop()

    def check_gpt_call(self, path):
        labels = [self.graph.nodes[node]['label'] for node in path]
        if self.is_valid_blueprint(labels):
            return self.create_gpt_call(labels)
        else:
            return None

    def is_valid_blueprint(self, labels):
        """Check if labels sequence matches the blueprint pattern."""
        return (len(labels) == 6 and labels[0] == 'user' and labels[2] == 'system' and labels[4] == 'user' and
                all(label not in ['user', 'system'] for label in [labels[1], labels[3], labels[5]]))


    def distribute_calls(self, matched_calls_handler, unmatched_calls_handler):
        matched, unmatched = self.classify_gpt_calls()

        # Process matched calls
        matched_calls_handler.process_calls(matched)

        # Process unmatched calls
        unmatched_calls_handler.process_calls(unmatched)
