import json

with open('smartrower_data.js', 'r', encoding='utf-8') as f:
    data = f.read().replace('const SMARTROWER_DATA = ', '').rstrip(';\n\r')
    
sessions = json.loads(data)
sessions.sort(key=lambda x: x.get('date', ''))
last_session = sessions[-1]

chart = last_session.get('smartrower', {}).get('chart', {})
hr_arr = chart.get('heart_rate', [])

print(f"Total valid HR points: {len([x for x in hr_arr if x is not None and x > 0])}")
print(f"Max HR overall: {last_session.get('stats', {}).get('max_hr')}")
