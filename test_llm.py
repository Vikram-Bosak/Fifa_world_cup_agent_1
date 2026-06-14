import os
import json
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

try:
    completion = client.chat.completions.create(
        model="meta/llama-3.1-70b-instruct",
        messages=[{"role": "user", "content": "Generate a 5 word hook about Zlatan Ibrahimovic."}],
        timeout=10
    )
    print("Success:", completion.choices[0].message.content)
except Exception as e:
    print("Error:", e)
