     query = """
        SELECT * FROM `enter-universes.graph_to_agent.nodes_table`
        WHERE graph_id = "20231114181549" AND STARTS_WITH(label, "@")
        """
