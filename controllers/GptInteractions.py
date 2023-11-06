 def extract_gpt_interactions_before_save(self, graph_data, graph_id):

        nodes_for_bq, edges_for_bq = self.translate_graph_data_for_bigquery(graph_data, graph_id)
        # Log the transformed data for debugging
        logger.debug(f"Transformed Nodes: {nodes_for_bq}")
        logger.debug(f"Transformed Edges: {edges_for_bq}")

        graph_data_as_dicts = {
            "nodes": nodes_for_bq,
            "edges": edges_for_bq
        }

        logger.debug(f"graph_data_as_dicts: {graph_data_as_dicts}")

        # Pass the dictionaries to the workflow logic
        processed_data = self.translate_graph_to_gpt_sequence(graph_data_as_dicts)

        processed_data = processed_data["processed_data"]
        logger.debug(f"processed_data: {processed_data}")
        agent_content = self.extract_and_send_to_gpt(processed_data)
        logger.debug(f"agent_content: {agent_content}")


    # Add the process_recursive_graph method
    def process_recursive_graph(self, graph_data):
        # Update valid transitions to include 'variable' nodes
        valid_transitions = {
            'user': 'content',
            'content': ['system', 'variable'],
            'system': 'content',
            'variable': 'content'
        }

        # Process the graph in a sequence
        processed_data = {"messages": []}
        variable_content = None

        for edge in graph_data["edges"]:
            from_node = graph_data["nodes"][edge['from']]
            to_node = graph_data["nodes"][edge['to']]

            from_node_type = self.get_node_type(from_node)
            to_node_type = self.get_node_type(to_node)

            # Check for valid transitions
            if valid_transitions[from_node_type] == to_node_type or to_node_type in valid_transitions[from_node_type]:
                if from_node_type == 'variable':
                    # Replace 'variable' node content with the previous GPT API response
                    from_node['label'] = variable_content

                # Add the interaction to the processed data
                processed_data['messages'].append({
                    "role": from_node_type,
                    "content": from_node['label']
                })

                # If the 'to' node is a 'variable', get response from GPT API
                if to_node_type == 'variable':
                    gpt_response = self.get_gpt_response(processed_data)
                    variable_content = gpt_response

        return processed_data

    # New method to interact with the GPT API
    def get_gpt_response(self, processed_data):
        post_data = {
            "model": os.getenv("MODEL"),
            "messages": processed_data["messages"]
        }
        response = requests.post(self.openai_base_url, headers=self.headers, json=post_data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Error in GPT request: {response.status_code}, {response.text}")
