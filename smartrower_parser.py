import os
import glob
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from scipy.interpolate import interp1d
import json
import warnings
warnings.filterwarnings('ignore')
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, "smartrower_downloads")
OUT_JS = os.path.join(BASE_DIR, "smartrower_data.js")

def parse_filename_date(filename):
    # SmartRower_Export_2026-06-04T17-12-48-131Z.csv
    match = re.search(r'(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})', filename)
    if match:
        return f"{match.group(1)} {match.group(2)}:{match.group(3)}:{match.group(4)}"
    return "Unknown Date"

def process_smartrower_csv(filepath):
    filename = os.path.basename(filepath)
    date_str = parse_filename_date(filename)
    
    metadata = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        metadata['title'] = f.readline().strip().replace('"', '')
        metadata['description'] = f.readline().strip().replace('"', '')
        f.readline()
        metadata['duration'] = f.readline().strip()
        f.readline()
        metadata['tss'] = f.readline().strip()
        
    df = pd.read_csv(filepath, skiprows=7)
    df['time_s'] = df['time_ms'] / 1000.0
    
    # Identify blocks
    df['block_id'] = (df['target_watts'].diff() != 0) | (df['target_spm'].diff() != 0) | (df['target_force'].diff() != 0)
    df['block_id'] = df['block_id'].cumsum()
    
    # Find strokes: usa cord_pos se funziona, altrimenti real_force
    cord_range = df['cord_pos'].max() - df['cord_pos'].min()
    cord_broken = False
    if cord_range > 10:
        peaks, _ = find_peaks(df['cord_pos'], distance=100, prominence=0.1)
    else:
        print(f"  cord_pos rotto (range={cord_range:.1f}m), rilevamento palate da real_force")
        # distance=120 (1.2s, max 50 SPM), height=15kgf (ignora i rimbalzi durante il recupero)
        peaks, _ = find_peaks(df['real_force'], distance=120, prominence=10, height=15)
        cord_broken = True

    # Fix per cord_pos rotto: ricalcola real_watts perché la macchina sottostima la distanza
    ROWER_HEIGHT_CM = 181
    L_STROKE = ROWER_HEIGHT_CM * 0.0137
    if cord_broken:
        print("  Ricalcolo real_watts basato su stroke length teorico (181cm)...")
        for i in range(len(peaks)-1):
            start_idx = peaks[i]
            end_idx = peaks[i+1]
            chunk = df.iloc[start_idx:end_idx]
            dt_s = chunk['time_s'].iloc[-1] - chunk['time_s'].iloc[0]
            if dt_s > 0.4: # Filtro falsi colpi troppo veloci
                drive = chunk[chunk['real_force'] > 2]
                f_mean = drive['real_force'].mean() if len(drive) > 0 else 0
                work_J = f_mean * 9.81 * L_STROKE
                power = work_J / dt_s
                df.loc[start_idx:end_idx, 'real_watts'] = min(power, 750)
            else:
                df.loc[start_idx:end_idx, 'real_watts'] = 0

    stroke_blocks = df['block_id'].iloc[peaks[:-1]].values
    spm = []
    peak_forces = []
    avg_watts_stroke = []

    raw_spm = []
    curves_by_spm = {}
    for i in range(len(peaks)-1):
        start_idx = peaks[i]
        end_idx = peaks[i+1]
        chunk = df.iloc[start_idx:end_idx]
        dt_s = chunk['time_s'].iloc[-1] - chunk['time_s'].iloc[0]
        dt_min = dt_s / 60.0
        raw_spm.append(1.0 / dt_min if dt_min > 0 else 0)
        peak_forces.append(chunk['real_force'].max())
        avg_watts_stroke.append(chunk['real_watts'].mean())

    # --- Extract Full Stroke Force Curves (Catch to Catch) using Robust Detection ---
    curves_by_spm = {}
    
    # Trova i veri picchi di forza per evitare falsi catch dovuti a rumore attorno a 1.0kg
    f_peaks, _ = find_peaks(df['real_force'].values, distance=100, prominence=5, height=10)
    catch_indices = []
    for p in f_peaks:
        c = p
        while c > 0 and df['real_force'].iloc[c] > 1.0:
            c -= 1
        if len(catch_indices) == 0 or c - catch_indices[-1] > 100:
            catch_indices.append(c)

    for i in range(1, len(catch_indices)-1):
        catch_idx = catch_indices[i]
        next_catch_idx = catch_indices[i+1]
        
        # Start 0.1s (10 samples) before catch
        start_idx = max(0, catch_idx - 10)
        end_idx = next_catch_idx - 10
        
        if end_idx <= start_idx:
            continue
            
        chunk = df.iloc[start_idx:end_idx]
        t_spm = int(chunk['target_spm'].iloc[0]) if 'target_spm' in chunk.columns else 0
        
        if t_spm > 0:
            if t_spm not in curves_by_spm:
                curves_by_spm[t_spm] = []
                
            y = chunk['real_force'].values
            if len(y) > 0:
                if len(y) < 300:
                    y = np.pad(y, (0, 300 - len(y)), 'constant', constant_values=0)
                else:
                    y = y[:300]
                
                y_downsampled = y[::5] # 60 points, 0.05s resolution
                curves_by_spm[t_spm].append(y_downsampled)

    # Filtro Outliers per SPM (es. colpi persi dal sensore rotto che generano SPM = 10)
    raw_s = pd.Series(raw_spm)
    raw_s = raw_s.where((raw_s >= 14) & (raw_s <= 55), np.nan)
    raw_s = raw_s.interpolate(limit_direction='both').fillna(0)
    
    # Media mobile a 3 colpi per gli SPM
    spm = raw_s.rolling(window=3, min_periods=1).mean().tolist()
    
    # Media mobile a 3 colpi per la forza di picco (Peak Force)
    pf_s = pd.Series(peak_forces)
    peak_forces = pf_s.rolling(window=3, min_periods=1).mean().tolist()

    # Process Average Force Curves by SPM Bucket
    force_curves_export = {}
    for t_spm, curves in curves_by_spm.items():
        if len(curves) >= 6: # Need some minimum strokes to be meaningful
            n = len(curves)
            c1 = curves[:n//3]
            c2 = curves[n//3:2*n//3]
            c3 = curves[2*n//3:]
            
            mid = np.mean(c2, axis=0).round(2).tolist() if len(c2)>0 else []
            peak_loc = round(np.argmax(mid) * 0.05, 2) if len(mid) > 0 else 0
            
            force_curves_export[str(t_spm)] = {
                "start": np.mean(c1, axis=0).round(2).tolist() if len(c1)>0 else [],
                "mid": mid,
                "end": np.mean(c3, axis=0).round(2).tolist() if len(c3)>0 else [],
                "peak_location_mid": peak_loc
            }

    strokes_df = pd.DataFrame({'block_id': stroke_blocks, 'spm': spm, 'peak_force': peak_forces})
    
    block_targets = df.groupby('block_id').agg({'time_s': ['min', 'max'], 'target_watts': 'first', 'target_spm': 'first', 'target_force': 'first'})
    block_targets.columns = ['time_start', 'time_end', 'target_watts', 'target_spm', 'target_force']
    block_targets['duration_min'] = (block_targets['time_end'] - block_targets['time_start']) / 60.0
    block_targets = block_targets[block_targets['duration_min'] > 0.16]
    
    block_reals = strokes_df.groupby('block_id').agg({'spm': 'mean', 'peak_force': 'mean'})
    block_reals.columns = ['real_spm', 'real_peak_force']
    
    # --- FIX SPECIFICO PER "Aerobic Capacity 2" ---
    if "Aerobic Capacity 2" in metadata['title']:
        print("Applicazione fix potenza da forza di picco per Aerobic Capacity 2...")
        df['real_watts'] = 0.0
        for i in range(len(peaks)-1):
            start_idx = peaks[i]
            end_idx = peaks[i+1]
            t_w = df['target_watts'].iloc[start_idx]
            t_f = df['target_force'].iloc[start_idx]
            r_pf = df['real_force'].iloc[start_idx:end_idx].max()
            if t_f > 0:
                df.loc[start_idx:end_idx, 'real_watts'] = t_w * (r_pf / t_f)
                
        # Re-calculate stroke avg_watts just in case
        avg_watts_stroke = []
        for i in range(len(peaks)-1):
            start_idx = peaks[i]
            end_idx = peaks[i+1]
            avg_watts_stroke.append(df['real_watts'].iloc[start_idx:end_idx].mean())
    # ----------------------------------------------

    # Filtro globale anti-spike: max 750W
    df['real_watts'] = df['real_watts'].clip(upper=750)

    df['sec_idx'] = df['time_s'].astype(int)
    df_sec = df.groupby('sec_idx').mean(numeric_only=True).reset_index()
    # Adherence
    active_mask = df_sec['target_watts'] > 0
    df_active = df_sec[active_mask]
    lower_bound = np.minimum(df_active['target_watts'] * 0.85, df_active['target_watts'] - 15)
    upper_bound = np.maximum(df_active['target_watts'] * 1.15, df_active['target_watts'] + 15)
    adherence_power = ((df_active['real_watts'] >= lower_bound) & (df_active['real_watts'] <= upper_bound)).mean() * 100

    blocks_summary = block_targets.join(block_reals).reset_index()
    
    blocks_out = []
    for _, row in blocks_summary.iterrows():
        if row['target_watts'] == 0: continue
        # Find real watts for this block
        block_sec = df_sec[(df_sec['sec_idx'] >= row['time_start']) & (df_sec['sec_idx'] <= row['time_end'])]
        real_w = block_sec['real_watts'].mean() if len(block_sec) > 0 else 0
        
        blocks_out.append({
            "time": f"{int(row['time_start']/60):02d}:{int(row['time_start']%60):02d} - {int(row['time_end']/60):02d}:{int(row['time_end']%60):02d}",
            "duration_min": round(row['duration_min'], 1),
            "target_watts": float(row['target_watts']),
            "real_watts": round(real_w, 1),
            "target_spm": float(row['target_spm']),
            "real_spm": round(row['real_spm'], 1) if pd.notnull(row['real_spm']) else 0,
            "target_force": float(row['target_force']),
            "real_peak_force": round(row['real_peak_force'], 1) if pd.notnull(row['real_peak_force']) else 0
        })

    # Subsample data for frontend charts (max ~500 points for real watts)
    # 1-second bins is fine
    chart_df = df_sec.iloc[::max(1, len(df_sec)//500)]
    
    # Stroke data (no downsampling per evitare aliasing del grafico SPM)
    stroke_t = df['time_s'].iloc[peaks[:-1]].values + (np.diff(df['time_s'].iloc[peaks]) / 2)
    
    # --- DISTANZA E CALORIE (modello teorico da altezza 181cm) ---
    ROWER_HEIGHT_CM = 181
    L_STROKE = ROWER_HEIGHT_CM * 0.0137  # stroke length teorico (m) calibrato su SmartRower
    
    stroke_power_theo = []
    for i in range(len(peaks)-1):
        start_idx = peaks[i]
        end_idx = peaks[i+1]
        chunk = df.iloc[start_idx:end_idx]
        dt_s = chunk['time_s'].iloc[-1] - chunk['time_s'].iloc[0]
        if dt_s <= 0:
            stroke_power_theo.append(0)
            continue
        drive = chunk[chunk['real_force'] > 2]  # fase di trazione (forza > 2 kgf)
        if len(drive) == 0:
            stroke_power_theo.append(0)
            continue
        f_mean = drive['real_force'].mean()
        work_J = f_mean * 9.81 * L_STROKE  # kgf -> N, poi * distanza
        stroke_power_theo.append(work_J / dt_s)
    
    # Distanza: formula Concept2  P = 2.80 / pace^3 => dist = sum(dt * (P/2.80)^(1/3))
    total_distance_m = 0
    total_work_J = 0
    for i in range(len(peaks)-1):
        dt_s = df['time_s'].iloc[peaks[i+1]] - df['time_s'].iloc[peaks[i]]
        p = stroke_power_theo[i]
        if dt_s > 0 and p > 0:
            total_distance_m += dt_s * (p / 2.80) ** (1.0/3.0)
            total_work_J += p * dt_s
    # Calorie: efficienza meccanica ~25%
    total_calories = total_work_J / 0.25 / 4186
    
    force_avg_power = np.mean([p for p in stroke_power_theo if p > 0]) if len(stroke_power_theo) > 0 else 0
    force_max_power = np.max(stroke_power_theo) if len(stroke_power_theo) > 0 else 0

    return {
        "filename": filename,
        "source": "smartrower",
        "date": date_str,
        "title": metadata['title'],
        "duration_min": round(df['time_s'].max() / 60.0, 1),
        "distance_m": round(total_distance_m, 0),
        "calories": round(total_calories, 0),
        "avg_power": round(df_active['real_watts'].mean(), 1),
        "max_power": round(df['real_watts'].max(), 1),
        "avg_hr": int(df_active['heart_rate'].mean()) if 'heart_rate' in df_active.columns and not df_active['heart_rate'].isna().all() else 0,
        "max_hr": int(df['heart_rate'].max()) if 'heart_rate' in df.columns and not df['heart_rate'].isna().all() else 0,
        "avg_cadence": round(np.mean(spm), 1) if len(spm)>0 else 0,
        "max_cadence": round(np.max(spm), 1) if len(spm)>0 else 0,
        "smartrower": {
            "tss": metadata['tss'],
            "avg_peak_force": round(np.mean(peak_forces), 1) if len(peak_forces)>0 else 0,
            "power_adherence_percent": round(adherence_power, 1),
            "blocks": blocks_out,
            "chart": {
                "time_s": chart_df['sec_idx'].tolist(),
                "target_watts": chart_df['target_watts'].tolist(),
                "real_watts": chart_df['real_watts'].tolist(),
                "target_spm": chart_df['target_spm'].tolist(),
                "target_force": chart_df['target_force'].tolist(),
                "heart_rate": chart_df['heart_rate'].where(pd.notnull(chart_df['heart_rate']), None).tolist() if 'heart_rate' in chart_df.columns else [],
                "stroke_t": stroke_t.tolist(),
                "stroke_spm": spm,
                "stroke_peak_force": peak_forces
            },
            "force_curves": force_curves_export
        }
    }

def main():
    results = []
    csv_files = glob.glob(os.path.join(CSV_DIR, "*.csv"))
    print(f"Found {len(csv_files)} SmartRower CSVs.")
    for f in csv_files:
        print(f"Processing {os.path.basename(f)}...")
        try:
            res = process_smartrower_csv(f)
            results.append(res)
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    # Sort descending by date
    results.sort(key=lambda x: x['date'], reverse=True)
    
    with open(OUT_JS, 'w', encoding='utf-8') as f:
        f.write("const SMARTROWER_DATA = " + json.dumps(results, indent=2) + ";\n")
    print(f"Wrote {OUT_JS} with {len(results)} sessions.")

if __name__ == "__main__":
    main()
