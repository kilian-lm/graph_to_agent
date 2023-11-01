import json

def get_schema(obj, key="root"):
    """Recursively derive the schema of a JSON object."""
    schema = {}

    if isinstance(obj, dict):
        schema[key] = {}
        for k, v in obj.items():
            schema[key].update(get_schema(v, k))
    elif isinstance(obj, list) and len(obj) > 0:
        schema[key] = []
        # for simplicity, assuming all items in the list have the same schema
        schema[key].append(get_schema(obj[0]))
    else:
        schema[key] = type(obj).__name__

    return schema

def load_json_and_get_schema(filename):
    """Load a JSON file and get its schema."""
    with open(filename, 'r') as f:
        data = json.load(f)
    return get_schema(data)

# Example Usage:
schema = load_json_and_get_schema('test.json')
schema2 = load_json_and_get_schema('agent_interactions_20231031_185854.json')
print(schema)
print(schema2)
