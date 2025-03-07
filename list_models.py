import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

response = requests.get(
    "https://api.openai.com/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)

if response.status_code == 200:
    models = response.json()["data"]
    for model in models:
        print(model["id"])
else:
    print(f"Error: {response.status_code}")
    print(response.text)