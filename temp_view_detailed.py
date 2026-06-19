import json

with open('smartrower_data.js', 'r', encoding='utf-8') as f:
    data = f.read().replace('const SMARTROWER_DATA = ', '').rstrip(';\n\r')
    
sessions = json.loads(data)
sessions.sort(key=lambda x: x.get('date', ''))

for i, s in enumerate(sessions[-2:]):
    print(f"[{i}] Title: {s.get('title')}")
    print(f"Date: {s.get('date')}")
    print(f"Duration: {s.get('duration_min')} min")
    print(f"Watts: {s.get('avg_power')}W, Max Watts: {s.get('max_power')}W")
    print(f"SPM: {s.get('avg_cadence')}, Max SPM: {s.get('max_cadence')}")
    print(f"HR: {s.get('avg_hr')} avg / {s.get('max_hr')} max")
    print(f"Peak Force Avg: {s.get('smartrower', {}).get('avg_peak_force')} kgf")
    
    chart = s.get('smartrower', {}).get('chart', {})
    hr_arr = chart.get('heart_rate', [])
    valid_hr = [x for x in hr_arr if x is not None and x > 0]
    if valid_hr:
        print(f"HR Start (first 60 valid pts): {sum(valid_hr[:60])/min(60, len(valid_hr)):.1f}")
        print(f"HR End (last 60 valid pts): {sum(valid_hr[-60:])/min(60, len(valid_hr)):.1f}")
    else:
        print("NO VALID HR DATA")
        
    print("---")
