import json
import os

from google.cloud import pubsub_v1
import json
import google.auth
from google.oauth2 import service_account

# Parsing the JSON credentials from the .env file
BQ_CLIENT_SECRETS = json.loads(os.environ.get("BQ_CLIENT_SECRETS"))

# Creating credentials from the parsed JSON
credentials = service_account.Credentials.from_service_account_info(BQ_CLIENT_SECRETS)

from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient(credentials=credentials)


import os
import json
from google.cloud import pubsub_v1
from google.oauth2 import service_account

class MainPublisher:
    def __init__(self, project_id, topic_name):
        # Parsing the JSON credentials from the .env file
        BQ_CLIENT_SECRETS = json.loads(os.environ.get("BQ_CLIENT_SECRETS"))

        # Creating credentials from the parsed JSON
        credentials = service_account.Credentials.from_service_account_info(BQ_CLIENT_SECRETS)

        # Pass the credentials to the PublisherClient
        self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
        self.topic_path = publisher.topic_path('enter-universes', 'enter-universes') # Replace 'your-project-id' with your Google Cloud Project ID


    def publish_message(self, message):
        try:
            message_dict = {'message': message}
            message_bytes = json.dumps(message_dict).encode('utf-8')
            future = self.publisher.publish(self.topic_path, data=message_bytes)
            message_id = future.result()
            print(f'Published message: {message_id}')
        except Exception as e:
            print(f'Error publishing message: {str(e)}')


# TODO :: get it running

# from google.cloud import pubsub_v1
#
# # Set up the client
# # publisher = pubsub_v1.PublisherClient()
# publisher = pubsub_v1.PublisherClient(credentials=credentials)
#
# topic_path = publisher.topic_path('enter-universes', 'enter-universes') # Replace 'your-project-id' with your Google Cloud Project ID
#
# def send_log(log_message):
#     # Send the log message
#     publisher.publish(topic_path, log_message.encode('utf-8'))
#
# # Sample log message
# log_message = "This is a sample log message."
# send_log(log_message)
#
# 1+1