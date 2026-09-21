import os
import requests

API_KEY = os.getenv("579b464db66ec23bdd0000014f8b8cd982924fd24e0e04e85fa2171e")

url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

params = {
    "api-key": API_KEY,
    "format": "json",
    "limit": 5,
    "filters[state.keyword]": "Maharashtra",
    "filters[commodity]": "Tomato"
}

response = requests.get(url, params=params, timeout=60)

print("Status:", response.status_code)
print(response.text[:5000])