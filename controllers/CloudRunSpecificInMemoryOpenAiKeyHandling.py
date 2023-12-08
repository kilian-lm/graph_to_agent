import os
import json

'''
I tried multiple approach to handle the OpenAI API key. The recurring problem is that whenever i call loops 
or need the key in a deeper class, the key is not available. If one stes the key via cloud run secrets, that works perfectly fine. 
But as i wanted the user to use own model with the graph agent approach, i considered this trade of and decided for a EULA pointing out the shortcomings
of the demo version and choosing the way via mounted in-memory in Cloud Run. 
If you run the app on a always on instance, get rid of this approach! 
'''


class CloudRunSpecificInMemoryOpenAiKeyHandling:
    def __init__(self):
        self.cache_dir = '/cache'  # Directory where the API key will be stored

    def save_api_key(self, api_key):
        # Check if the /cache directory exists, and create it if not
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # Write the API key to a JSON file in /cache
        with open(os.path.join(self.cache_dir, 'api_key.json'), 'w') as file:
            json.dump({'api_key': api_key}, file)

    def get_api_key(self):
        # Read the API key from the JSON file in /cache
        api_key_file = os.path.join(self.cache_dir, 'api_key.json')
        if os.path.exists(api_key_file):
            with open(api_key_file, 'r') as file:
                data = json.load(file)
                return data.get('api_key')
        return None
