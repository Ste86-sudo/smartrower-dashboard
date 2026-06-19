import json

with open('smartrower_data.js', 'r', encoding='utf-8') as f:
    data = f.read().replace('const SMARTROWER_DATA = ', '').rstrip(';\n\r')
    
sessions = json.loads(data)
sessions.sort(key=lambda x: x.get('date', ''))
last_session = sessions[-1]

chart = last_session.get('smartrower', {}).get('chart', {})
time_s = chart.get('time_s', [])
real_watts = chart.get('real_watts', [])
target_watts = chart.get('target_watts', [])
hr_arr = chart.get('heart_rate', [])

# find intervals where target_watts is high (>200W or so)
intervals = []
in_interval = False
start_idx = 0
for i in range(len(target_watts)):
    if target_watts[i] > 180 and not in_interval:
        in_interval = True
        start_idx = i
    elif target_watts[i] <= 180 and in_interval:
        in_interval = False
        intervals.append((start_idx, i))

print("High Intensity Intervals:")
for idx, (s, e) in enumerate(intervals):
    dur = time_s[e-1] - time_s[s]
    avg_w = sum(real_watts[s:e]) / (e-s)
    valid_hr = [x for x in hr_arr[s:e] if x is not None and x > 0]
    max_h = max(valid_hr) if valid_hr else 0
    print(f"Interval {idx+1}: {dur}s | Watts: {avg_w:.1f}W | Max HR: {max_h}")

