import os, json, shutil
from agents.market_price_agent.market_price_agent import get_market_prices

key = os.getenv('DATA_GOV_API_KEY')
print(json.dumps({
    'has_key': bool(key),
    'curl_present': bool(shutil.which('curl.exe')),
    'government_url': 'https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070',
    'sample_result': get_market_prices('Wheat', 'Madhya Pradesh')
}, ensure_ascii=True))
