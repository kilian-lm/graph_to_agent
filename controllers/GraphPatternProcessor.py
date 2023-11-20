from controllers.VariableConnectedComponentsProcessor import VariableConnectedComponentsProcessor

class GraphPatternProcessor(VariableConnectedComponentsProcessor):
    def __init__(self, graph, num_steps):
        self.graph = graph
        self.num_steps = num_steps
        self.bq_client = bigquery.Client()

    def process_graph(self):
        """Main method to process the graph."""
        user_nodes = [node for node, attrs in self.graph.nodes(data=True) if attrs['label'] == 'user']
        for start_node in user_nodes:
            for path in self.explore_paths(start_node, steps=self.num_steps):
                self.check_and_print_gpt_call(path)

    def explore_paths(self, start_node, steps):
        """Explore all paths up to a certain number of steps from a start node."""
        paths = []
        self.dfs(start_node, [], steps, paths)
        return paths

    def dfs(self, node, path, steps, paths):
        """Depth-first search to explore paths."""
        if steps == 0 or node in path:
            return
        path.append(node)
        if len(path) == steps + 1:
            paths.append(path.copy())
        else:
            for neighbor in self.graph.neighbors(node):
                self.dfs(neighbor, path, steps - 1, paths)
        path.pop()

    def is_valid_blueprint(self, labels):
        """Check if labels sequence matches the blueprint pattern."""
        return (len(labels) == 6 and labels[0] == 'user' and labels[2] == 'system' and labels[4] == 'user' and
                all(label not in ['user', 'system'] for label in [labels[1], labels[3], labels[5]]))

    def save_gpt_calls_to_jsonl(self, file_path, graph_id):
        """Save GPT calls to a JSON Lines file with additional UUID and graph_id."""
        with open(file_path, 'w') as file:
            user_nodes = [node for node, attrs in self.graph.nodes(data=True) if attrs['label'] == 'user']
            for start_node in user_nodes:
                # Generate a UUID for each component path
                path_uuid = str(uuid.uuid4())
                for path in self.explore_paths(start_node, steps=self.num_steps):
                    gpt_call, is_valid = self.generate_gpt_call_json(path, path_uuid, graph_id)
                    if is_valid:
                        json_line = json.dumps(gpt_call)
                        file.write(json_line + '\n')

    def generate_gpt_call_json(self, path, path_uuid, graph_id):
        """Generate a JSON representation of a GPT call with UUID and graph_id."""
        labels = [self.graph.nodes[node]['label'] for node in path]
        if self.is_valid_blueprint(labels):
            gpt_call_json = {
                "path": path,
                "gpt_call": {
                    "model": "gpt-4",
                    "messages": [
                        {"role": "user", "content": labels[1]},
                        {"role": "system", "content": labels[3]},
                        {"role": "user", "content": labels[5]}
                    ]
                },
                "answer_node": {
                    "node_id": f"answer_{path[-1]}",
                    "label": self.get_answer_label(path)
                },
                "uuid": path_uuid,
                "graph_id": graph_id
            }
            return gpt_call_json, True
        return {}, False

    def get_answer_label(self, path):
        """Get the label for the answer node, considering @variable terms."""
        # Find @variable nodes
        variable_nodes = self.find_variable_nodes()
        components_with_variables = self.find_connected_components_with_variables(variable_nodes)

        # Check if any node in the path is part of a connected component with @variables
        for component in components_with_variables:
            if any(node in path for node in component):
                for node in component:
                    if node in variable_nodes:
                        return self.graph.nodes[node]['label']

        return "None"

    def dump_to_bigquery(self, file_path, dataset_name, table_name):
        """Upload the JSONL data to BigQuery."""
        client = bigquery.Client()
        table_id = f"{client.project}.{dataset_name}.{table_name}"

        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            autodetect=True
        )

        # Load the JSONL file to BigQuery
        with open(file_path, "rb") as source_file:
            job = client.load_table_from_file(source_file, table_id, job_config=job_config)

        # Wait for the load job to complete
        job.result()

        print(f"Uploaded {file_path} to {table_id}")
