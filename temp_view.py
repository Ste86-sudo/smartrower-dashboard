import json

with open('smartrower_data.js', 'r', encoding='utf-8') as f:
    data = f.read().replace('const SMARTROWER_DATA = ', '').rstrip(';\n\r')
    
sessions = json.loads(data)
sessions.sort(key=lambda x: x.get('date', ''))

for i, s in enumerate(sessions[-3:]):
    print(f"Title: {s.get('title', 'N/A')}")
    print(f"Date: {s.get('date', 'N/A')}")
    stats = s.get('stats', {})
    print(f"Watts: {stats.get('avg_watts', 'N/A')}W, SPM: {stats.get('avg_cadence', 'N/A')}")
    print(f"HR: {stats.get('avg_hr', 'N/A')} avg / {stats.get('max_hr', 'N/A')} max")
    print(f"Duration: {s.get('duration_min', 'N/A')} min")
    print("---")
