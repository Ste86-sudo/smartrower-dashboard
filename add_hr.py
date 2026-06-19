import json
import fitparse
import numpy as np
import datetime
from scipy import signal
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

# The latest session is data[0] (Aerobic Capacity 6)
session = data[0]
chart = session['smartrower']['chart']
time_s = np.array(chart['time_s'])
real_watts = np.array(chart['real_watts'])

# Create 1 Hz interpolated signals
max_time = int(np.max(time_s))
t_1hz = np.arange(0, max_time + 1)
watts_1hz = np.interp(t_1hz, time_s, real_watts)

# HR is already ~1Hz in FIT file (1 sample per second usually)
# Let's assume HR is 1Hz. We will correlate watts_1hz and hr_data.
# Normalize signals for cross-correlation
w_norm = watts_1hz - np.mean(watts_1hz)
hr_norm = hr_data - np.mean(hr_data)

print("Calcolo cross-correlazione...")
correlation = signal.correlate(hr_norm, w_norm, mode='full')
lags = signal.correlation_lags(len(hr_norm), len(w_norm), mode='full')

best_lag = lags[np.argmax(correlation)]
print(f"Miglior allineamento: HR spostato di {best_lag} secondi rispetto alla potenza.")

# Positive lag means HR array is shifted "right" compared to Watts array.
# Which means hr_data[i] corresponds to watts_1hz[i - best_lag]
# Let's map HR back to the original time_s array of the rowing session!

aligned_hr = []
for t in time_s:
    hr_idx = int(t + best_lag)
    if 0 <= hr_idx < len(hr_data):
        aligned_hr.append(hr_data[hr_idx])
    else:
        aligned_hr.append(None) # Out of bounds

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
