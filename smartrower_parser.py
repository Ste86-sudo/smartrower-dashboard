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

# ─────────────────────────────────────────────────────────────────────────────
# COSTANTI FISICHE E DI CALIBRAZIONE  (fonte: HANDOFF_brief_SmartRowerPro §3-4)
# V-Fit Tornado Air = aria quasi pura, NO serranda → F = b2·v² + F0 (modello fisso).
# Tutte PROVVISORIE finché il FW non logga 3 canali a 100 Hz reali, encoder pulito
# sub-mm, ritardo forza↔posizione compensato e seat_pos attivo (brief §7).
# ─────────────────────────────────────────────────────────────────────────────
SAMPLE_HZ        = 100          # 10 ms nominali fra i campioni
KG_TO_N          = 9.81         # real_force è in kg → Newton

# Lunghezza del drive (corsa utile). MISURATA dalla cord_pos corretta (~1.16-1.25 m,
# brief §4.3), NON dalla vecchia formula altezza·0.0137 = 2.48 m che era ~2× troppo
# lunga e gonfiava lavoro/potenza/distanza. Quando cord_pos è vivo si usa il valore
# misurato per-sessione; altrimenti questo default.
L_DRIVE_DEFAULT_M = 1.20
B2_PROVV         = 110.0        # N·s²/m²  coeff. aria pura (PROVVISORIO ±20%, range 100-125)
F0_PROVV         = 18.0         # N        offset corda elastica (k≈0, M_eff≈0)

# Ritardo FISSO di acquisizione forza↔posizione (cella wireless vs encoder).
# Su erg ad aria forza e velocità sono simultanee → è un offset di acquisizione,
# NON fisica. Va sottratto prima di QUALSIASI metrica posizione-dipendente
# (posizione-picco, catch factor). Innocuo per metriche a canale singolo. (brief §4.5)
FORCE_LAG_MS     = 200          # range utile 150-300; best fit aria-pura a ~210 ms
FORCE_LAG_SAMPLES = int(round(FORCE_LAG_MS / 1000.0 * SAMPLE_HZ))   # = 20 @100 Hz

# Segmentazione vogata: la fullness è ipersensibile alla soglia. Una soglia alta
# (es. 8 kg) TAGLIA LE CODE e gonfia la fullness a ~0.76 (artefatto). Usare una
# soglia BASSA ancorata alla tara reale → fullness ~0.62 (range elite). (brief §4.1)
TARA_MARGIN_KG   = 1.5          # soglia drive = tara + margine
TARA_PCTL        = 5            # la tara è stimata come 5° percentile della forza

# Riferimento di scala puleggia (file 8 giu, diametro corretto): correzione lineare
# α = p95_attivo_rif / p95_attivo_misurato. Verifica indipendente sui massimi
# (CORD_MAX_REF/max_misurato) deve concordare entro ~3%. (brief §4.2-4.3)
CORD_P95_REF_M   = 0.890        # p95 di cord_pos con forza attiva (>15 kg)
CORD_MAX_REF_M   = 1.41         # corsa massima di riferimento
CORD_PLAUSIBLE_MAX_M = 1.6      # oltre questo la scala puleggia è quasi certamente errata

# Bug 1 Hz (brief §4.6 #1): forza/cord, pur a timestamp 10 ms, restano congelate per
# ~100 campioni → dati effettivi a 1 Hz, una vogata ≈ 1 campione → inutilizzabile.
FREEZE_RUN_SAMPLES = 50         # run di valori identici ≥ questo durante l'attività = sospetto


def estimate_tara(force, active_mask=None):
    """Baseline (tara) della cella come percentile basso della forza a riposo."""
    f = force[~active_mask] if active_mask is not None and (~active_mask).any() else force
    return float(np.percentile(f, TARA_PCTL))


def detect_sampling_freeze(series, active_idx):
    """Rileva il bug di campionamento 1 Hz: valori 'congelati' per molti campioni
    consecutivi DURANTE l'attività. Ritorna (is_frozen, hold_mediano_campioni).
    Ignora i lunghi tratti a riposo (inizio/fine) usando solo gli indici attivi."""
    if len(active_idx) < 50:
        return False, 0
    s = np.asarray(series)[active_idx]
    # lunghezze dei run di campioni identici consecutivi
    change = np.diff(s) != 0
    runs, cur = [], 1
    for c in change:
        if c:
            runs.append(cur); cur = 1
        else:
            cur += 1
    runs.append(cur)
    runs = np.array(runs)
    hold_med = float(np.median(runs)) if len(runs) else 0.0
    # se il run mediano durante l'attività è grande, il segnale vive a 1 Hz
    is_frozen = hold_med >= FREEZE_RUN_SAMPLES
    return is_frozen, hold_med


# Banda entro cui un cord_pos fuori scala è plausibilmente un errore LINEARE di
# diametro puleggia (correggibile con α). Oltre, il canale è rotto / in altra unità
# (es. contatore grezzo) e NON va riscalato — va solo segnalato come morto.
CORD_SCALE_ERR_MAX_M = 5.0
CORD_REF_FORCE_KG    = 15.0     # il p95 di riferimento (0.890 m) è definito a forza>15 kg


def compute_pulley_alpha(cord_pos, force_kg):
    """Fattore di correzione lineare della scala puleggia (errore di diametro).
    Ritorna (alpha, p95_meas, max_meas, coerente). alpha=1.0 se la scala è già
    plausibile, se cord_pos è morto, o se è fuori scala in modo NON lineare
    (canale rotto) → in quel caso non si tocca."""
    cp = np.asarray(cord_pos)
    rng = cp.max() - cp.min()
    cmax = float(cp.max())
    if rng < 0.1:
        return 1.0, 0.0, cmax, None                      # cord_pos morto (tutto 0)
    if cmax <= CORD_PLAUSIBLE_MAX_M:
        return 1.0, float(np.percentile(cp, 95)), cmax, None   # scala già plausibile
    if cmax > CORD_SCALE_ERR_MAX_M:
        return 1.0, float(np.percentile(cp, 95)), cmax, False  # canale rotto, non riscalare
    # p95 con la STESSA definizione del riferimento: solo campioni a forza alta
    hi = np.asarray(force_kg) > CORD_REF_FORCE_KG
    p95 = float(np.percentile(cp[hi], 95)) if hi.any() else float(np.percentile(cp, 95))
    if p95 <= 0:
        return 1.0, p95, cmax, None
    alpha = CORD_P95_REF_M / p95
    # verifica indipendente sui massimi: deve concordare entro ~5% (brief §4.3)
    alpha_max = CORD_MAX_REF_M / cmax if cmax > 0 else alpha
    coerente = abs(alpha - alpha_max) / alpha < 0.05
    return alpha, p95, cmax, bool(coerente)

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

    # ── CALIBRAZIONE E QUALITÀ DEL DATO (HANDOFF_brief §4) ──────────────────────
    force_kg = df['real_force'].values
    tara_kg = estimate_tara(force_kg)                      # baseline cella (~1.5 kg)
    seg_threshold = tara_kg + TARA_MARGIN_KG               # soglia drive ancorata alla tara
    active_mask = force_kg > seg_threshold
    active_idx = np.where(active_mask)[0]

    # Correzione lineare della scala puleggia (se cord_pos vivo e fuori scala)
    alpha, cord_p95, cord_max, alpha_coerente = compute_pulley_alpha(df['cord_pos'].values, force_kg)
    # Applica la correzione SOLO se i due stimatori indipendenti (p95 e max) concordano
    # entro ~5%: è la condizione che il brief usa per fidarsi di un errore di scala
    # LINEARE pulito (§4.3). Se discordano, meglio non introdurre errore.
    if alpha != 1.0 and alpha_coerente:
        df['cord_pos'] = df['cord_pos'] * alpha
        print(f"  Scala puleggia corretta: alpha={alpha:.3f} (p95={cord_p95:.3f}->{cord_p95*alpha:.3f} m, coerente_su_max=True)")
    elif alpha != 1.0:
        print(f"  Scala puleggia NON corretta: stime p95/max discordi (alpha_p95={alpha:.3f}, max={cord_max:.2f} m) -> lascio cord_pos invariato")
        alpha = 1.0

    # Diagnostica bug di acquisizione (brief §4.6)
    force_frozen, force_hold = detect_sampling_freeze(force_kg, active_idx)
    # cord usabile = vivo, in metri plausibili (dopo eventuale correzione α) e non
    # un canale rotto/altra-unità (max enorme non riscalato).
    cord_span = df['cord_pos'].max() - df['cord_pos'].min()
    cord_alive = bool(0.1 < cord_span < CORD_PLAUSIBLE_MAX_M * 1.1 and df['cord_pos'].max() < CORD_PLAUSIBLE_MAX_M * 1.1)
    cord_frozen, cord_hold = (detect_sampling_freeze(df['cord_pos'].values, active_idx)
                              if cord_alive else (False, 0.0))
    seat_alive = bool((df['seat_pos'].max() - df['seat_pos'].min()) > 0.02)

    data_quality = {
        "tara_kg": round(tara_kg, 2),
        "seg_threshold_kg": round(seg_threshold, 2),
        "sampling_1hz_bug": bool(force_frozen or cord_frozen),   # valori congelati ~1 Hz
        "force_hold_samples": round(force_hold, 1),
        "cord_pos_alive": bool(cord_alive),
        "cord_pos_frozen": bool(cord_frozen),
        "seat_pos_alive": seat_alive,                            # serve per catch factor / sequenza
        "pulley_alpha": round(alpha, 3),
        "pulley_scale_coherent": alpha_coerente,
        # b2 e la potenza istantanea sono affidabili solo con 100 Hz veri + ritardo
        # compensato + cord pulito. Qui segnaliamo se la finestra è calibrabile.
        "b2_calibratable": bool(cord_alive and not force_frozen and not cord_frozen),
    }
    if data_quality["sampling_1hz_bug"]:
        print(f"  [!] Bug campionamento 1 Hz rilevato (hold~{max(force_hold, cord_hold):.0f} campioni): metriche posizionali inaffidabili.")
    if not seat_alive:
        print("  [!] seat_pos = 0: niente catch factor ne analisi di sequenza (sellino).")

    # Serie forza COMPENSATA del ritardo fisso forza↔posizione: la forza arriva
    # ~200 ms dopo la posizione, quindi la anticipiamo prima di accoppiarla alla
    # posizione. Solo per metriche posizione-dipendenti (NON per il picco in tempo,
    # SPM, L_drive ecc., che sono immuni — brief §4.5).
    df['force_lagcomp'] = df['real_force'].shift(-FORCE_LAG_SAMPLES).bfill()

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

    # Lunghezza del drive: MISURATA dalla cord_pos corretta quando il canale è usabile
    # (mediana della corsa per vogata), altrimenti il default 1.20 m (brief §4.3).
    L_drive_m = None
    if cord_alive:
        cp_arr = df['cord_pos'].values
        spans = []
        for i in range(len(peaks) - 1):
            seg = cp_arr[peaks[i]:peaks[i+1]]
            dmask = force_kg[peaks[i]:peaks[i+1]] > seg_threshold
            if dmask.sum() >= 3:
                s = seg[dmask].max() - seg[dmask].min()
                if 0.2 < s < CORD_PLAUSIBLE_MAX_M:
                    spans.append(s)
        if len(spans) >= 10:
            L_drive_m = round(float(np.median(spans)), 3)
    L_STROKE = L_drive_m if L_drive_m is not None else L_DRIVE_DEFAULT_M

    # Fix per cord_pos rotto: ricalcola real_watts (la macchina sottostima la distanza)
    if cord_broken:
        print(f"  Ricalcolo real_watts con L_drive={L_STROKE:.2f} m...")
        for i in range(len(peaks)-1):
            start_idx = peaks[i]
            end_idx = peaks[i+1]
            chunk = df.iloc[start_idx:end_idx]
            dt_s = chunk['time_s'].iloc[-1] - chunk['time_s'].iloc[0]
            if dt_s > 0.4: # Filtro falsi colpi troppo veloci
                drive = chunk[chunk['real_force'] > 2]
                f_mean = drive['real_force'].mean() if len(drive) > 0 else 0
                work_J = f_mean * KG_TO_N * L_STROKE
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
    catch_factors_by_spm = {}
    
    # Trova i veri picchi di forza per evitare falsi catch dovuti a rumore attorno a 1.0kg
    f_peaks, _ = find_peaks(df['real_force'].values, distance=100, prominence=5, height=10)
    catch_indices = []
    for p in f_peaks:
        c = p
        # cammina indietro fino alla baseline reale (tara), non a un magico 1.0 kg
        while c > 0 and df['real_force'].iloc[c] > seg_threshold:
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
                catch_factors_by_spm[t_spm] = []
                
            y = chunk['real_force'].values
            
            # Estrazione Catch Factor (solo se ENTRAMBI i canali posizione sono validi:
            # seat attivo e cord usabile — niente catch factor su un cord rotto).
            if seat_alive and cord_alive:
                w_start = max(0, catch_idx - 50)
                w_end = min(len(df), catch_idx + 50)
                if w_end > w_start:
                    seat_window = df['seat_pos'].iloc[w_start:w_end].values
                    cord_window = df['cord_pos'].iloc[w_start:w_end].values
                    time_window = df['time_ms'].iloc[w_start:w_end].values
                    
                    if (seat_window.max() - seat_window.min()) > 0.05 and (cord_window.max() - cord_window.min()) > 0.001:
                        seat_min_idx = np.argmin(seat_window)
                        cord_min_val = cord_window.min()
                        min_indices = np.where(cord_window <= cord_min_val + 0.001)[0]
                        if len(min_indices) > 0:
                            cord_min_idx = min_indices[-1]
                            t_seat = time_window[seat_min_idx]
                            t_cord = time_window[cord_min_idx]
                            catch_factors_by_spm[t_spm].append(float(t_seat - t_cord))

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

            # Fullness e posizione-picco% sulla curva media, con soglia drive ancorata
            # alla tara (NON F_peak*0.1 né soglie alte → niente artefatto, brief §4.1).
            fullness = None
            peak_pos_pct = None
            if len(mid) > 0:
                arr = np.array(mid)
                di = np.where(arr > seg_threshold)[0]
                fpk = arr.max()
                # Servono un drive di durata sensata E un ritorno a baseline dentro la
                # finestra (curva NON tutta sopra soglia = vogata fusa/tagliata → scarta).
                if 4 <= len(di) <= 0.9 * len(arr) and fpk > 0:
                    fullness = round(float(arr[di].mean() / fpk), 3)
                    peak_pos_pct = round(float((np.argmax(arr) - di[0]) / (di[-1] - di[0])), 3)
                    # fullness fisica < ~0.85 (l'artefatto peggiore del brief era 0.76).
                    # Oltre = bucket degenere/poche vogate → meglio non riportare nulla.
                    if fullness > 0.85:
                        fullness = None
                        peak_pos_pct = None

            cf_median = None
            if t_spm in catch_factors_by_spm and len(catch_factors_by_spm[t_spm]) > 0:
                cf_median = float(np.median(catch_factors_by_spm[t_spm]))

            force_curves_export[str(t_spm)] = {
                "start": np.mean(c1, axis=0).round(2).tolist() if len(c1)>0 else [],
                "mid": mid,
                "end": np.mean(c3, axis=0).round(2).tolist() if len(c3)>0 else [],
                "peak_location_mid": peak_loc,
                "fullness": fullness,                 # ~0.62 elite; alto+soglia-bassa = front/back-load
                "peak_pos_pct": peak_pos_pct,         # frazione del drive (in tempo) al picco
                "catch_factor_ms": round(cf_median, 1) if cf_median is not None else None
            }

    strokes_df = pd.DataFrame({'block_id': stroke_blocks, 'spm': spm, 'peak_force': peak_forces})
    
    block_targets = df.groupby('block_id').agg({'time_s': ['min', 'max'], 'target_watts': 'first', 'target_spm': 'first', 'target_force': 'first'})
    block_targets.columns = ['time_start', 'time_end', 'target_watts', 'target_spm', 'target_force']
    block_targets['duration_min'] = (block_targets['time_end'] - block_targets['time_start']) / 60.0
    block_targets = block_targets[block_targets['duration_min'] > 0.16]
    
    block_reals = strokes_df.groupby('block_id').agg({'spm': 'mean', 'peak_force': 'mean'})
    block_reals.columns = ['real_spm', 'real_peak_force']
    
    # --- FIX POTENZA (ERG MODE / CORD_BROKEN) ---
    # Dato che target_watts = target_force * (costante, di solito ~4.0)
    # Se il sensore di distanza è rotto, ricalcoliamo i real_watts linearmente basandoci sul rapporto tra
    # real_peak_force e target_force per garantire la coerenza con le aspettative dell'utente.
    if cord_broken:
        print("  Applicazione fix potenza lineare basato su real_peak_force...")
        df['real_watts'] = 0.0
        for i in range(len(peaks)-1):
            start_idx = peaks[i]
            end_idx = peaks[i+1]
            t_w = df['target_watts'].iloc[start_idx]
            t_f = df['target_force'].iloc[start_idx]
            r_pf = df['real_force'].iloc[start_idx:end_idx].max()
            if t_f > 0 and t_w > 0:
                # Applica il ratio del blocco corrente
                df.loc[start_idx:end_idx, 'real_watts'] = t_w * (r_pf / t_f)
            else:
                # Fallback: ratio standard di 4.0 se non ci sono target
                df.loc[start_idx:end_idx, 'real_watts'] = r_pf * 4.0
                
        # Ricalcola la media dei watts per vogata
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
    
    # --- DISTANZA E CALORIE (usa L_drive misurato/default, vedi sopra) ---
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

    # --- FISICA POSIZIONALE ROBUSTA (brief §4.3): lavoro = ∫F·dx sul drive ---
    # Potenza = lavoro/T_ciclo con la corsa REALE della corda. È un integrale di
    # posizione → immune al jitter di velocità e al ritardo forza↔posizione.
    # L_drive_m (mediana per-vogata) è già stato misurato sopra; lo riportiamo solo
    # se la finestra è davvero calibrabile (100 Hz veri, cord pulito).
    power_pos_W = None
    L_drive_phys = L_drive_m if data_quality["b2_calibratable"] else None
    if L_drive_phys is not None:
        cp = df['cord_pos'].values
        p_list = []
        for i in range(len(peaks) - 1):
            s, e = peaks[i], peaks[i + 1]
            chunk_f = force_kg[s:e]
            dmask = chunk_f > seg_threshold
            if dmask.sum() < 3:
                continue
            l_drive = cp[s:e][dmask].max() - cp[s:e][dmask].min()
            dt_s = (df['time_s'].iloc[e] - df['time_s'].iloc[s])
            if 0.2 < l_drive < CORD_PLAUSIBLE_MAX_M and dt_s > 0.4:
                p_list.append(chunk_f[dmask].mean() * KG_TO_N * l_drive / dt_s)
        if len(p_list) >= 10:
            power_pos_W = round(float(np.median(p_list)), 1)

    physics = {
        "model": "F = b2*v^2 + F0 (aria pura, V-Fit Tornado)",
        "b2_provv": B2_PROVV,
        "F0_provv": F0_PROVV,
        "force_lag_ms": FORCE_LAG_MS,
        "pulley_alpha": round(alpha, 3),
        "L_drive_m": L_drive_m,            # corsa reale del drive misurata (None se cord non usabile)
        "L_drive_source": "misurato" if L_drive_m is not None else "default",
        "L_drive_used_m": L_STROKE,        # valore effettivamente usato per potenza/distanza
        "power_position_W": power_pos_W,   # potenza da ∫F·dx, lag-immune (PROVVISORIA)
        "provvisorio": True,               # vale finché valgono i caveat del brief §7
    }

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
            "force_curves": force_curves_export,
            "data_quality": data_quality,
            "physics": physics
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
