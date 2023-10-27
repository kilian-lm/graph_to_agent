import json
import os

from google.cloud import pubsub_v1


class MainPublisher:
    def __init__(self, project_id, topic_name, user_id):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_name)
        self.user_id = user_id

    def publish_message(self, message):
        try:
            message_dict = {'user_id': self.user_id, 'message': message}
            message_bytes = json.dumps(message_dict).encode('utf-8')
            future = self.publisher.publish(self.topic_path, data=message_bytes)
            message_id = future.result()
            print(f'Published message: {message_id}')
        except Exception as e:
            print(f'Error publishing message: {str(e)}')
