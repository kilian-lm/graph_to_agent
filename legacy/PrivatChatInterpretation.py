from google.cloud import bigquery
from typing import Any, Dict, List
import json
import os

from controllers.BigQueryHandler import BigQueryHandler

class JSONSchemaParser:
    def __init__(self, file_path: str, dataset_name: str, table_name: str):
        self.file_path = file_path
        self.bq_client = BigQueryHandler('PrivatChatInterpretation').bigquery_client
        self.dataset_name = dataset_name
        self.table_name = table_name
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

    def determine_schema(self, key: str, value: Any) -> bigquery.SchemaField:
        if isinstance(value, dict):
            return bigquery.SchemaField(key, 'RECORD', mode='REPEATED' if isinstance(value, list) else 'NULLABLE', fields=self.process_subitem(value))
        elif isinstance(value, list):
            if value:
                return bigquery.SchemaField(key, self.get_data_type(value[0]), mode='REPEATED')
            else:
                return bigquery.SchemaField(key, 'STRING', mode='REPEATED')
        else:
            return bigquery.SchemaField(key, self.get_data_type(value))

    def process_subitem(self, item: Dict[str, Any]) -> List[bigquery.SchemaField]:
        sub_schema = []
        for sub_key, sub_value in item.items():
            sub_schema.append(self.determine_schema(sub_key, sub_value))
        return sub_schema

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

    def create_table(self):
        dataset_ref = self.bq_client.dataset(self.dataset_name)
        table_ref = dataset_ref.table(self.table_name)
        table = bigquery.Table(table_ref, schema=self.schema)
        table = self.bq_client.create_table(table)
        print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")

    def upload_data(self):
        table_id = f"{self.bq_client.project}.{self.dataset_name}.{self.table_name}"
        job_config = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON)
        with open(self.file_path, "rb") as source_file:
            job = self.bq_client.load_table_from_file(source_file, table_id, job_config=job_config)

        job.result()  # Wait for the job to complete
        print(f"Loaded {job.output_rows} rows into {table_id}")

# Example usage
dataset_name = 'open_ai_chat_hist'
table_name = 'open_ai_chat_hist_20231210'
file_path = 'privat_chat_hist/conversations.json'

parser = JSONSchemaParser(file_path, dataset_name, table_name)
parser.parse()
parser.create_table()
1+1
parser.upload_data()
1+2
