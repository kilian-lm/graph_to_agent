import openai

openai.api_key = 'your-api-key'  # Replace with your actual API key

assistant = openai.Assistant.create(
    name="Math Tutor",
    description="You are a personal math tutor. Write and run code to answer math questions.",
    training_data=[
        {
            "prompt": "What's 2 + 2?",
            "completion": "The answer is 4."
        },
        # Add more training examples if necessary
    ],
    settings={
        "tools": [{"type": "code_interpreter"}]
    },
    model="gpt-4-1106-preview"  # Replace with the actual model you are using
)

print(assistant)
