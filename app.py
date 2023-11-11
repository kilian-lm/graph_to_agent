import os
import datetime
from flask import Flask, render_template, jsonify, request
import json
# from controllers.GptAgentInteractions import GptAgentInteractions
from controllers.v2GptAgentInteractions import v2GptAgentInteractions


from logger.CustomLogger import CustomLogger
import logging

app = Flask(__name__)

# gpt_agent_interactions = GptAgentInteractions('graph_to_agent')


class App():
    def __init__(self):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        print(timestamp)
        self.log_file = f'{timestamp}_app.log'
        print(self.log_file)
        self.log_dir = './temp_log'
        print(self.log_dir)
        self.log_level = logging.DEBUG
        print(self.log_level)
        self.logger = CustomLogger(self.log_file, self.log_level, self.log_dir)

        self.app = Flask(__name__)
        # self.gpt_agent_interactions = GptAgentInteractions('graph_to_agent')
        self.gpt_agent_interactions = v2GptAgentInteractions('graph_to_agent')
        self.setup_routes()

    def index_call(self):
        return render_template('graph.html')

    def get_graph_data(self):
        try:
            graph_id = request.json['graph_id']
            graph_data = self.gpt_agent_interactions.load_graph_data_by_id(graph_id)
            return jsonify(graph_data)
        except Exception as e:
            self.logger.error(f"Error fetching graph data: {e}")
            return jsonify({"status": "error", "message": str(e)})

    def get_available_graphs(self):
        try:
            available_graphs = self.gpt_agent_interactions.get_available_graphs()
            return jsonify(available_graphs)
        except Exception as e:
            self.logger.error(f"Error loading available graphs: {e}")
            return jsonify({"status": "error", "message": str(e)})

    def return_gpt_agent_answer_to_graph(self):
        graph_data = request.json
        self.logger.info(f"return_gpt_agent_answer_to_graph, graph_data: {graph_data}")
        gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data)
        print(gpt_response)
        # breakpoint()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"temp_local/debugging_var_method_{timestamp}.json"

        # Check if the temp_local directory exists
        if not os.path.exists('temp_local'):
            os.makedirs('temp_local')

        # Save the JSON data to the file
        with open(filename, 'w') as json_file:
            json_file.write(json.dumps(graph_data))  # Serialize dict to JSON formatted string

        processed_data = self.gpt_agent_interactions.translate_graph_to_gpt_sequence(graph_data)
        self.logger.info(f"return_gpt_agent_answer_to_graph, processed_data: {processed_data}")

        # Identify if any @variable placeholders are present
        variable_node_present = any('@variable' in node['label'] for node in graph_data['nodes'])
        self.logger.info(f"return_gpt_agent_answer_to_graph, variable_node_present: {variable_node_present}")

        if variable_node_present:
            # Call the populate_variable_nodes method
            # Note: You need to obtain the initial GPT response to populate the base @variable
            initial_gpt_response = self.gpt_agent_interactions.extract_and_send_to_gpt(processed_data)
            self.logger.info(f"return_gpt_agent_answer_to_graph, initial_gpt_response: {initial_gpt_response}")
            updated_graph = self.gpt_agent_interactions.populate_variable_nodes(graph_data, initial_gpt_response)
            self.logger.info(f"return_gpt_agent_answer_to_graph, updated_graph: {updated_graph}")

        else:
            # Continue with the legacy workflow
            # gpt_response = self.gpt_agent_interactions.extract_and_send_to_gpt(processed_data)

            # gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data)
            # gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data_json)
            gpt_response = self.gpt_agent_interactions.main_tree_based_design_general(graph_data)

            self.logger.info(f"return_gpt_agent_answer_to_graph, gpt_response: {gpt_response}")
            updated_graph = self.gpt_agent_interactions.process_gpt_response_and_update_graph(gpt_response, graph_data)
            self.logger.info(f"return_gpt_agent_answer_to_graph, updated_graph: {updated_graph}")

        return jsonify({"status": "success", "updatedGraph": updated_graph})

    # except Exception as e:
    #     self.logger.error(f"Error processing GPT agent request: {e}")
    #     return jsonify({"status": "error", "message": str(e)})

    # def return_gpt_agent_answer_to_graph(self):
    #     try:
    #         graph_data = request.json
    #         self.logger.info(f"return_gpt_agent_answer_to_graph, graph_data: {graph_data}")
    #         processed_data = self.gpt_agent_interactions.translate_graph_to_gpt_sequence(graph_data)
    #         self.logger.info(f"return_gpt_agent_answer_to_graph, processed_data: {processed_data}")
    #
    #         # todo :: check via if else for @variable node, if no var, than legacy workflow
    #         self.gpt_agent_interactions.populate_variable_nodes()
    #
    #
    #         gpt_response = self.gpt_agent_interactions.extract_and_send_to_gpt(processed_data)
    #         self.logger.info(f"return_gpt_agent_answer_to_graph, gpt_response: {gpt_response}")
    #
    #         updated_graph = self.gpt_agent_interactions.process_gpt_response_and_update_graph(gpt_response, graph_data)
    #         self.logger.info(f"return_gpt_agent_answer_to_graph, updated_graph: {updated_graph}")
    #
    #         return jsonify({"status": "success", "updatedGraph": updated_graph})
    #     except Exception as e:
    #         self.logger.error(f"Error processing GPT agent request: {e}")
    #         return jsonify({"status": "error", "message": str(e)})

    def save_graph(self):
        try:
            graph_data = request.json
            self.logger.info(f"save_graph, graph_data: {graph_data}")

            graph_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            self.logger.info(f"save_graph, graph_id: {graph_id}")
            errors = self.gpt_agent_interactions.save_graph_data(graph_data, graph_id)

            self.logger.error(f"save_graph, errors: {errors}")

            if errors:
                return jsonify({"status": "error", "message": "Failed to save some data.", "errors": errors})

            return jsonify({"status": "success", "message": "Graph saved successfully!"})
        except Exception as e:
            self.logger.error(f"Error saving graph: {e}")
            return jsonify({"status": "error", "message": str(e)})

    def setup_routes(self):
        self.app.route('/')(self.index_call)
        self.app.route('/get-graph-data', methods=['POST'])(self.get_graph_data)
        self.app.route('/get-available-graphs', methods=['GET'])(self.get_available_graphs)
        self.app.route('/return-gpt-agent-answer-to-graph', methods=['POST'])(self.return_gpt_agent_answer_to_graph)
        self.app.route('/save-graph', methods=['POST'])(self.save_graph)

    def run(self):
        self.app.run(debug=True)


if __name__ == '__main__':
    server = App()
    server.run()
