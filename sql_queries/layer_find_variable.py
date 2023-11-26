LAYER_FIND_VARIABLE = """
        SELECT * FROM `{tbl_ref}`
        WHERE graph_id = "{graph_id}" AND STARTS_WITH(label, "@")
        """

# 20231114181549

# `enter-universes.graph_to_agent.nodes_table`
