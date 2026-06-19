import json
import pandas as pd

with open('smartrower_data.js', 'r', encoding='utf-8') as f:
    data = f.read().replace('const SMARTROWER_DATA = ', '').rstrip(';\n\r')
    
sessions = json.loads(data)
sessions.sort(key=lambda x: x.get('date', ''))
last_session = sessions[-1]

print(f"Title: {last_session['title']}")
print(f"Date: {last_session['date']}")
print("Intervals:")

telemetry = last_session.get('telemetry', {})
time_s = telemetry.get('time_s', [])
real_watts = telemetry.get('real_watts', [])
target_watts = telemetry.get('target_watts', [])
heart_rate = telemetry.get('heart_rate', [])

if time_s:
    df = pd.DataFrame({'time_s': time_s, 'real_watts': real_watts, 'target_watts': target_watts, 'heart_rate': heart_rate})
    df['block'] = (df['target_watts'] != df['target_watts'].shift()).cumsum()
    blocks = df.groupby('block').agg(
        start_time=('time_s', 'min'),
        end_time=('time_s', 'max'),
        target=('target_watts', 'first'),
        real_avg=('real_watts', 'mean'),
        hr_max=('heart_rate', 'max'),
        hr_avg=('heart_rate', 'mean')
    )
    for idx, row in blocks.iterrows():
        dur = row['end_time'] - row['start_time']
        print(f"Block {idx}: Dur {dur:.1f}s | Target {row['target']:.1f}W | Real {row['real_avg']:.1f}W | HR Avg {row['hr_avg']:.1f} Max {row['hr_max']}")
