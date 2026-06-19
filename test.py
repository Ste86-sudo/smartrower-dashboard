import json
with open('smartrower_data.js', encoding='utf-8') as f:
  s=f.read().replace('const SMARTROWER_DATA = ', '').replace(';', '')
  data=json.loads(s)
  for i in range(2):
    d = data[i]
    print(f"Session {i}: {d['title']}, {d['date']}")
    print(f"  Dur: {d['duration_min']}m, Dist: {d['distance_m']}m, Cal: {d['calories']}")
    print(f"  Avg W: {d['avg_power']}, Max W: {d['max_power']}")
    print(f"  Avg SPM: {d['avg_cadence']}, Max SPM: {d['max_cadence']}")
    print(f"  Peak F: {d['smartrower']['avg_peak_force']}")
    if 'blocks' in d['smartrower']:
       print(f"  Blocks:")
       for b in d['smartrower']['blocks']:
           print(f"    {b['time']} | tgt W: {b['target_watts']} real W: {b['real_watts']} | tgt SPM: {b['target_spm']} real: {b['real_spm']}")
