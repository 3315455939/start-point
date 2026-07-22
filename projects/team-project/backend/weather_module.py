import os
import json
import datetime
import requests

DATA_DIR = os.path.join(os.path.expanduser("~"), ".desktop_tools")
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_API_KEY = os.environ.get("OWM_API_KEY", "")

def fetch_weather(city, api_key=None, timeout=10):
    """调用 OpenWeatherMap 获取天气，返回 JSON dict。"""
    if not api_key:
        api_key = DEFAULT_API_KEY
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
        'lang': 'zh_cn'
    }
    resp = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    save_weather_history(city, data)
    return data

def history_path():
    return os.path.join(DATA_DIR, "weather_history.json")

def save_weather_history(city, data):
    try:
        history = load_weather_history() or []
    except:
        history = []
    record = {
        'city': city,
        'temp': round(data.get('main', {}).get('temp', 0)),
        'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'data': data
    }
    history = [r for r in history if r.get('city') != city]
    history.insert(0, record)
    history = history[:10]
    with open(history_path(), 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_weather_history():
    try:
        with open(history_path(), 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []
