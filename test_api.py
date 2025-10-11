import requests
from config import NEWSAPI_KEY

url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWSAPI_KEY}"

response = requests.get(url)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
