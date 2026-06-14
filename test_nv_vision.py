import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.getenv("NVIDIA_API_KEY")
)

try:
    response = client.chat.completions.create(
      model="microsoft/phi-3-vision-128k-instruct",
      messages=[
        {
          "role": "user",
          "content": "Hello"
        }
      ],
      max_tokens=100,
    )
    print("Phi3 Success:", response.choices[0].message.content)
except Exception as e:
    print("Phi3 Error:", e)

