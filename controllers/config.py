# config.py

import os

class Config:
    # Your OpenAI API key
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
