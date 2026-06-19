import json
import fitparse
import numpy as np
import datetime
import os

print("Lettura FIT file...")
fit = fitparse.FitFile(r'C:\Users\stefa\Downloads\Zepp20260615194001.fit')
hr_data = []
for record in fit.get_messages('record'):
    h = record.get_value('heart_rate')
    if h:
        hr_data.append(h)
hr_data = np.array(hr_data, dtype=float)

print("Lettura smartrower_data.js...")
with open('smartrower_data.js', 'r', encoding='utf-8') as f:
    content = f.read()
    json_str = content.replace('const SMARTROWER_DATA = ', '').replace(';', '')
    data = json.loads(json_str)

session = data[0]
chart = session['smartrower']['chart']
time_s = np.array(chart['time_s'])

# Find end of the rowing session (max time_s)
end_of_session_time = int(np.max(time_s))

# Find the point where HR drops below 150 BPM towards the end of the trace.
# We will look backwards from the end, find where it is < 150, but we want the "first time it drops below 150 towards the end".
# Let's find the absolute maximum peak, and then search forward from there to find the first time it drops below 150.
max_hr_idx = np.argmax(hr_data)
drop_idx = max_hr_idx
for i in range(max_hr_idx, len(hr_data)):
    if hr_data[i] < 150:
        drop_idx = i
        break

print(f"Max HR at index {max_hr_idx}, drops below 150 at index {drop_idx}")

# The user wants to align `drop_idx` (in HR time) with `end_of_session_time` (in rowing time).
# So hr_data[drop_idx] should map to time_s = end_of_session_time.
# This means HR time 0 corresponds to rowing time = end_of_session_time - drop_idx.
# Therefore, hr_idx = rowing_time - (end_of_session_time - drop_idx)
# hr_idx = rowing_time - end_of_session_time + drop_idx

offset = drop_idx - end_of_session_time - 10
print(f"Offset calcolato (con -10s): {offset}")

aligned_hr = []
for t in time_s:
    hr_idx = int(t + offset)
    
    # "e taglia i dati dopo quando lo plotti"
    # This means any rowing time after end_of_session_time (which corresponds to hr_idx > drop_idx) 
    # should NOT have HR data. Wait, time_s goes up to end_of_session_time, so the HR data will naturally stop there anyway.
    # However, if there are points right at the end, we should just enforce hr_idx <= drop_idx.
    if 0 <= hr_idx <= drop_idx:
        aligned_hr.append(hr_data[hr_idx])
    else:
        aligned_hr.append(None)

chart['heart_rate'] = aligned_hr

# Calculate Avg and Max HR for the session
valid_hrs = [h for h in aligned_hr if h is not None]
if valid_hrs:
    session['avg_hr'] = int(np.mean(valid_hrs))
    session['max_hr'] = int(np.max(valid_hrs))
    print(f"Avg HR: {session['avg_hr']}, Max HR: {session['max_hr']}")

# Save back to js
with open('smartrower_data.js', 'w', encoding='utf-8') as f:
    f.write('const SMARTROWER_DATA = ' + json.dumps(data, separators=(',', ':')) + ';')

print("Fatto!")
