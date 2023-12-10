# test
import json
from typing import Any, Dict, List

class JSONSchemaParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = self.read_json_file()
        self.schema = []

    def read_json_file(self) -> Any:
        with open(self.file_path, 'r') as file:
            return json.load(file)

    def parse(self):
        if isinstance(self.data, list):
            for item in self.data:
                self.process_item(item)
        else:
            self.process_item(self.data)

    def process_item(self, item: Dict[str, Any]):
        for key, value in item.items():
            self.schema.append(self.determine_schema(key, value))

    def determine_schema(self, key: str, value: Any) -> Dict[str, str]:
        if isinstance(value, dict):
            return {key: 'RECORD'}
        elif isinstance(value, list):
            return {key: 'REPEATED'}
        else:
            return {key: self.get_data_type(value)}

    @staticmethod
    def get_data_type(value: Any) -> str:
        if isinstance(value, int):
            return 'INTEGER'
        elif isinstance(value, float):
            return 'FLOAT'
        elif isinstance(value, bool):
            return 'BOOLEAN'
        else:
            return 'STRING'

    def get_schema(self) -> List[Dict[str, str]]:
        return self.schema

# Example usage
file_path = 'privat_chat_hist/conversations.json'
parser = JSONSchemaParser(file_path)
parser.parse()
schema = parser.get_schema()
print(schema)
