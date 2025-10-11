from sentiment_analyzer import MarketSentimentAnalyzer
from config import NEWSAPI_KEY
import requests

# Quick test with top business headlines
url = f"https://newsapi.org/v2/top-headlines?category=business&country=us&apiKey={NEWSAPI_KEY}"
response = requests.get(url)
print(f"Status: {response.status_code}")
articles = response.json().get('articles', [])
print(f"Found {len(articles)} business headlines")
for i, article in enumerate(articles[:3], 1):
    print(f"{i}. {article['title']}")
