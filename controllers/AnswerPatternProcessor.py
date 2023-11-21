"""SELECT
  gc.graph_id,
  gc.uuid,
  gc.answer_node.label AS answer_label,
  gc.answer_node.node_id AS answer_node_id,
  message.content,
  message.role,
  gc.gpt_call.model
FROM
  `enter-universes.graph_to_agent_chat_completions.test_2` gc,
  UNNEST(gpt_call.messages) as message
WHERE
  CAST(gc.graph_id AS STRING) = '20231117163236'"""

open_ai_url = "https://api.openai.com/v1/chat/completions"

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {openai_api_key}'
}

def extract_variables(content):
    """Extract @variable tags from the content."""
    return re.findall(r"@variable_\d+_\d+", content)

def process_gpt_request_for_uuid(data, uuid):
    """Process GPT request for a specific UUID and update the DataFrame."""
    group = data[data['uuid'] == uuid]
    messages = [{"role": r["role"], "content": r["content"]} for _, r in group.iterrows()]
    model = group.iloc[0]['model']

    # Send GPT request
    request_data = {
        "model": model,
        "messages": messages
    }
    response = requests.post(open_ai_url, headers=headers, json=request_data)
    response_json = response.json()
    response_content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")

    # Update the DataFrame with the response
    last_index = group.index[-1]
    data.at[last_index, 'answer_label'] = response_content
    return response_content

# Extract and sort all @variable tags
variable_tags = defaultdict(list)
for index, row in data.iterrows():
    variables = extract_variables(row['content'])
    for var in variables:
        variable_tags[var].append((row['uuid'], index))

sorted_variables = sorted(variable_tags.keys(), key=lambda x: (int(x.split('_')[1]), int(x.split('_')[2])))

# Process each @variable in sorted order
variable_responses = {}
for var in sorted_variables:
    uuids = set([uuid for uuid, _ in variable_tags[var]])
    for uuid in uuids:
        response = process_gpt_request_for_uuid(data, uuid)
        variable_responses[var] = response

    # Update the DataFrame with the response for this and higher suffix variables
    for higher_var in sorted_variables[sorted_variables.index(var) + 1:]:
        for higher_uuid, _ in variable_tags[higher_var]:
            data.loc[data['uuid'] == higher_uuid, 'content'] = data[data['uuid'] == higher_uuid]['content'].apply(
                lambda x: x.replace(var, variable_responses[var])
            )

    def dump_to_bq_jsonl(self, graph_id, uuid, response_json):
        # Create table name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        table_id = f"{self.dataset_id}.graph_id_{graph_id}_generated_answer_{timestamp}"

        # Prepare data for insertion in jsonl format
        data = json.dumps({
            "uuid": uuid,
            "response_id": response_json.get('id', ''),
            "model": response_json.get('model', ''),
            "content": response_json,
            "created_at": datetime.fromtimestamp(response_json.get('created', 0))
        }) + "\n"  # Adding newline for jsonl format

        # Define job configuration
        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        job_config.autodetect = True

        # Load data to BigQuery
        load_job = self.client.load_table_from_json(
            json_rows=[data], destination=table_id, job_config=job_config
        )
        load_job.result()  # Wait for the job to complete

        # Check for errors
        if load_job.errors:
            raise Exception(f"Encountered errors while inserting data: {load_job.errors}")
