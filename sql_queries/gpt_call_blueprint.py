GPT_CALL_BLUEPRINT = """SELECT
  gc.graph_id,
  gc.uuid,
  gc.answer_node.label AS answer_label,
  gc.answer_node.node_id AS answer_node_id,
  message.content,
  message.role,
  gc.gpt_call.model
FROM
  `{tbl_ref}` gc,
  UNNEST(gpt_call.messages) as message
WHERE
  CAST(gc.graph_id AS STRING) = '{graph_id}'"""

#   `enter-universes.graph_to_agent_chat_completions.test_2` gc,
#   CAST(gc.graph_id AS STRING) = '20231117163236'"""
