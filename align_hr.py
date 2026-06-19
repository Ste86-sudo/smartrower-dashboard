import json
import fitparse
import numpy as np

print("Lettura FIT file...")
fit = fitparse.FitFile(r'C:\Users\stefa\.gemini\antigravity\scratch\exr_analyzer\smartrower_downloads\Zepp20260615194001.fit')
hr_data = []
for record in fit.get_messages('record'):
    h = record.get_value('heart_rate')
    if h:
        hr_data.append(h)
hr_data = np.array(hr_data, dtype=float)

print("Lettura smartrower_data.js...")
with open('smartrower_data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Safe JSON extraction
prefix = 'const SMARTROWER_DATA = '
if content.startswith(prefix):
    json_str = content[len(prefix):].strip()
    if json_str.endswith(';'):
        json_str = json_str[:-1]
    data = json.loads(json_str)
else:
    raise ValueError("Formato smartrower_data.js inatteso")

# Find the specific session
session_idx = -1
for i, d in enumerate(data):
    if d['title'] == 'Aerobic Capacity 6' and '2026-06-15' in d['date']:
        session_idx = i
        break

if session_idx == -1:
    raise ValueError("Sessione Aerobic Capacity 6 non trovata!")

session = data[session_idx]
print(f"Trovata sessione: {session['title']} in data {session['date']} all'indice {session_idx}")

chart = session['smartrower']['chart']
time_s = np.array(chart['time_s'])

end_of_session_time = int(np.max(time_s))

max_hr_idx = np.argmax(hr_data)
drop_idx = max_hr_idx
for i in range(max_hr_idx, len(hr_data)):
    if hr_data[i] < 150:
        drop_idx = i
        break

print(f"Max HR at index {max_hr_idx}, drops below 150 at index {drop_idx}")

offset = drop_idx - end_of_session_time - 10
print(f"Offset calcolato (con -10s): {offset}")

aligned_hr = []
for t in time_s:
    hr_idx = int(t + offset)
    if 0 <= hr_idx <= drop_idx:
        aligned_hr.append(int(hr_data[hr_idx]))
    else:
        aligned_hr.append(None)

chart['heart_rate'] = aligned_hr

valid_hrs = [h for h in aligned_hr if h is not None]
if valid_hrs:
    session['avg_hr'] = int(np.mean(valid_hrs))
    session['max_hr'] = int(np.max(valid_hrs))
    print(f"Avg HR: {session['avg_hr']}, Max HR: {session['max_hr']}")

with open('smartrower_data.js', 'w', encoding='utf-8') as f:
    # Use json.dumps without minifying totally to avoid issues, or standard dump
    f.write('const SMARTROWER_DATA = ' + json.dumps(data, indent=2) + ';\n')

print("Fatto! Dati salvati.")
