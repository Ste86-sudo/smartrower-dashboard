"""
biomechanics.py — Motore di analisi biomeccanica del gesto di voga (3 segnali).

Implementa le metriche validate in letteratura descritte nel riferimento tecnico
"Biomeccanica del Canottaggio: Curva di Forza, Tirata al Manubrio, Corsa del Sellino"
(Kleshnev/Biorow, Holt et al. 2020, Warmenhoven et al. 2017-18, Dudhia).

Segnali di ingresso (dal CSV SmartRower a 100 Hz):
  - real_force  [kgf]  cella di carico sul manubrio           -> curva di forza
  - cord_pos    [m]    encoder sulla corda (draw del manubrio) -> posizione/velocita'
  - seat_pos    [m]    ToF sul sellino                         -> coordinazione/sequenza

FILOSOFIA "quality-aware": ogni metrica viene calcolata SOLO se i segnali che le
servono sono vivi e affidabili nella sessione. La forza e' quasi sempre valida; la
posizione (corda) e la coordinazione (sellino) spesso no. Il chiamante passa i flag
di qualita' gia' stimati dal parser; qui si rispettano scrupolosamente.

Ogni metrica esce con: valore, banda di riferimento (dal documento) e un giudizio
graduato ('ottimo' | 'buono' | 'da_migliorare') + un cue di coaching mirato.

Le curve ensemble sono normalizzate PER FASE (catch = 0%, finish = 100%), come
raccomandato dal documento (Warmenhoven, cap. 6) — piu' robuste del campionamento a
tempo fisso perche' vogate di durata diversa restano confrontabili.
"""

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# COSTANTI DI RIFERIMENTO (dal documento). Sono i target biomeccanici, NON tarature
# hardware — quelle restano nel parser. I valori assoluti di forza (N) di elite
# on-water non sono confrontabili 1:1 con un erg ad aria amatoriale (cap. 4/Caveats),
# quindi qui pesano soprattutto FORMA e COORDINAZIONE, che trasferiscono meglio.
# ─────────────────────────────────────────────────────────────────────────────
KG_TO_N = 9.81

# Fullness R = F_media/F_picco. Reale 0.40-0.60 (Kleshnev); stile sequenziale ~0.50,
# simultaneo ~0.70. Banda "sana" per erg amatoriale a colpo sequenziale.  (cap. 1)
FULLNESS_LOW   = 0.50
FULLNESS_HIGH  = 0.65
FULLNESS_MAX_PHYS = 0.85   # oltre = artefatto di segmentazione, si scarta

# Posizione del picco di forza come % del drive. Ideale 32-40% (Kleshnev/RP3). (cap. 1)
PEAK_POS_LOW   = 0.32
PEAK_POS_HIGH  = 0.40

# Catch Factor (ms): T0_sellino − T0_manubrio. Ottimo −15 (scull) / −25 (sweep).
# < −50 ms = "shooting the slide" (slitta che scappa). > +? ms = "opening up"/grabbing. (cap. 3)
CF_OPT_SCULL_MS  = -15.0
CF_SHOOT_MS      = -50.0    # sotto questo: perdita di potenza significativa
CF_POS_GRAB_MS   = 30.0     # sopra: apertura/strappo (manubrio in ritardo sul sellino)

# Rowing Style Factor: corsa sellino/corsa manubrio nel primo 20% del drive.
# Ottimo ~90%; <80% "grabbing"; >100% "bum-shoving".  (cap. 3)
RSF_OPT        = 0.90
RSF_GRAB       = 0.80
RSF_SHOVE      = 1.00

# Drive:recovery ratio. Avanzati ~1:2 (0.5); erg osservato 0.37-0.53, cresce con lo SPM. (cap. 2)
DR_LOW         = 0.33
DR_HIGH        = 0.55

# Drive length tipico su Concept2: 1.2-1.4 m; su questo erg ~1.0-1.2 m (corda). (cap. 2)

N_CURVE = 50   # punti della curva ensemble normalizzata per fase (0..100% del drive)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY
# ─────────────────────────────────────────────────────────────────────────────
def _grade(value, low, high, higher_is_better=None, in_band_is_best=True):
    """Giudizio graduato rispetto a una banda [low, high].
    in_band_is_best=True: dentro banda = ottimo, poco fuori = buono, molto fuori = da_migliorare."""
    if value is None:
        return None
    if in_band_is_best:
        if low <= value <= high:
            return "ottimo"
        # tolleranza del 25% della larghezza banda per "buono"
        tol = 0.25 * (high - low) if high > low else abs(high) * 0.1
        if (low - tol) <= value <= (high + tol):
            return "buono"
        return "da_migliorare"
    return None


def _resample_phase(y, n=N_CURVE):
    """Ricampiona un segmento (una fase drive) su n punti equispaziati in % di fase."""
    y = np.asarray(y, dtype=float)
    if len(y) < 2:
        return None
    xp = np.linspace(0, 1, len(y))
    xq = np.linspace(0, 1, n)
    return np.interp(xq, xp, y)


def detect_catches(force_kg, seg_threshold, min_gap=100, prominence=5, height=15):
    """Indici di 'catch' (inizio drive) camminando indietro dai picchi di forza fino
    alla baseline reale (tara), non a una soglia magica. min_gap in campioni."""
    from scipy.signal import find_peaks
    f = np.asarray(force_kg)
    f_peaks, _ = find_peaks(f, distance=min_gap, prominence=prominence, height=height)
    catches = []
    for p in f_peaks:
        c = p
        while c > 0 and f[c] > seg_threshold:
            c -= 1
        if not catches or c - catches[-1] > min_gap:
            catches.append(c)
    return np.array(catches, dtype=int), f_peaks


# ─────────────────────────────────────────────────────────────────────────────
# METRICHE PER SINGOLA VOGATA
# ─────────────────────────────────────────────────────────────────────────────
def stroke_metrics(force_kg, cord, seat, time_s, seg_threshold,
                   cord_alive, seat_alive):
    """Metriche di UNA vogata dal catch (i0) al catch successivo (i1), passata come
    slice gia' ritagliata. Ritorna dict (campi None dove il segnale non lo consente)."""
    f = np.asarray(force_kg, dtype=float)
    t = np.asarray(time_s, dtype=float)
    if len(f) < 5:
        return None

    # Fase di drive: dalla prima risalita sopra soglia all'ultimo campione sopra soglia.
    drive = np.where(f > seg_threshold)[0]
    if len(drive) < 4:
        return None
    d0, d1 = int(drive[0]), int(drive[-1])
    if d1 <= d0:
        return None

    fdrive = f[d0:d1 + 1]
    tdrive = t[d0:d1 + 1]
    t_drive = float(tdrive[-1] - tdrive[0])
    t_stroke = float(t[-1] - t[0])
    if t_drive <= 0.1 or t_stroke <= 0.2:
        return None

    f_peak = float(fdrive.max())
    f_mean = float(fdrive.mean())
    if f_peak <= 0:
        return None

    # Impulso ∫F·dt sul drive (N·s)
    impulse = float(np.trapz(fdrive * KG_TO_N, tdrive))

    # Posizione del picco come % di TEMPO del drive: single-channel (solo forza),
    # quindi immune al ritardo forza↔posizione non calibrato. La versione posizionale
    # (% di corsa) richiederebbe la compensazione del lag e resta sperimentale.
    # Holt et al. riportano analogamente il "tempo al picco". (cap. 1, cap. 6)
    ipk = int(np.argmax(fdrive))
    peak_pos = float((tdrive[ipk] - tdrive[0]) / t_drive)
    peak_pos_source = "tempo"
    # posizione picco in % di corsa (sperimentale, se corda viva)
    peak_pos_xpct = None
    if cord_alive and cord is not None:
        cpd0 = np.asarray(cord, dtype=float)[d0:d1 + 1]
        span0 = cpd0.max() - cpd0.min()
        if span0 > 0.2:
            peak_pos_xpct = round(min(max(float((cpd0[ipk] - cpd0.min()) / span0), 0.0), 1.0), 3)

    # RFD: pendenza iniziale della curva (N/s) sul tratto catch→picco. (cap. 1)
    t_to_peak = float(tdrive[ipk] - tdrive[0])
    rfd = float((f_peak - fdrive[0]) * KG_TO_N / t_to_peak) if t_to_peak > 0.02 else None

    # Fullness R = F_media/F_picco
    fullness = round(f_mean / f_peak, 3)

    out = {
        "f_peak_kg": round(f_peak, 1),
        "f_peak_n": round(f_peak * KG_TO_N, 0),
        "f_mean_kg": round(f_mean, 1),
        "impulse_ns": round(impulse, 1),
        "t_drive_s": round(t_drive, 3),
        "t_stroke_s": round(t_stroke, 3),
        "fullness": fullness,
        "peak_pos": round(peak_pos, 3),
        "peak_pos_source": peak_pos_source,
        "peak_pos_xpct": peak_pos_xpct,
        "rfd_ns": round(rfd, 0) if rfd is not None else None,
        # riempiti sotto se i segnali lo consentono
        "drive_length_m": None,
        "dr_ratio": None,
        "catch_factor_ms": None,
        "rsf": None,
        "fp_curve": None,   # curva forza-posizione normalizzata (per ensemble)
    }

    # Drive:recovery ratio (indipendente dalla corda): drive/recupero in tempo.
    t_recovery = t_stroke - t_drive
    if t_recovery > 0.1:
        out["dr_ratio"] = round(t_drive / t_recovery, 3)

    # ── Metriche che richiedono la CORDA (posizione manubrio) ──────────────────
    # NB: l'encoder di questa corda e' quantizzato a gradini (~mm, aggiornamenti a
    # scatti). Il DRIVE LENGTH (span robusto) e la CURVA forza-posizione MEDIATA su
    # molte vogate sono affidabili; la velocita' istantanea del manubrio e lo slip/wash
    # per-vogata NO (differenziare un segnale a gradini amplifica il rumore), quindi
    # non vengono riportati finche' l'encoder non e' piu' fine (cap. 6, Fase-1).
    if cord_alive and cord is not None:
        cp = np.asarray(cord, dtype=float)
        cpd = cp[d0:d1 + 1]
        span = float(cpd.max() - cpd.min())
        if 0.2 < span < 1.6:
            out["drive_length_m"] = round(span, 3)
            # Curva forza-POSIZIONE normalizzata: F vs frazione di corsa (0..1). (cap. 6)
            x = (cpd - cpd.min()) / span
            order = np.argsort(x)
            xq = np.linspace(0, 1, N_CURVE)
            out["fp_curve"] = np.interp(xq, x[order], fdrive[order]).round(2).tolist()

    # ── Metriche di COORDINAZIONE: servono corda + sellino ─────────────────────
    if cord_alive and seat_alive and cord is not None and seat is not None:
        cp = np.asarray(cord, dtype=float)
        sp = np.asarray(seat, dtype=float)
        # T0h: inversione del manubrio = minimo della corda (catch). (cap. 6)
        # T0s: inversione del sellino = minimo del sellino (piu' compresso al catch).
        # Finestra attorno al catch (inizio slice) per stimare i due zero-crossing.
        w = slice(0, min(len(t), max(d0 + 20, 40)))
        cw, sw, tw = cp[w], sp[w], t[w]
        if len(cw) > 5 and (cw.max() - cw.min()) > 0.02 and (sw.max() - sw.min()) > 0.03:
            # minimo corda: ultimo indice al minimo (fine recupero / catch)
            cmin = cw.min()
            ch_idx = np.where(cw <= cmin + 0.005)[0]
            t0h = tw[ch_idx[-1]] if len(ch_idx) else tw[np.argmin(cw)]
            t0s = tw[int(np.argmin(sw))]
            cf_ms = float((t0s - t0h) * 1000.0)
            if -300 < cf_ms < 300:   # scarta glitch impossibili
                out["catch_factor_ms"] = round(cf_ms, 1)

        # RSF: Δsellino/Δmanubrio nel primo 20% del drive. (cap. 3)
        cpd = cp[d0:d1 + 1]
        spd = sp[d0:d1 + 1]
        n20 = max(2, int(0.20 * len(cpd)))
        d_cord = abs(cpd[n20] - cpd[0]) if n20 < len(cpd) else 0.0
        d_seat = abs(spd[n20] - spd[0]) if n20 < len(spd) else 0.0
        if d_cord > 0.01:
            out["rsf"] = round(min(d_seat / d_cord, 2.0), 3)

    return out


# ─────────────────────────────────────────────────────────────────────────────
# AGGREGAZIONE ENSEMBLE PER BUCKET DI SPM
# ─────────────────────────────────────────────────────────────────────────────
def _median(vals):
    vals = [v for v in vals if v is not None]
    return float(np.median(vals)) if vals else None


def ensemble_by_spm(strokes, min_strokes=6, coordination_calibrated=False):
    """Aggrega le metriche per bucket di SPM target. Ritorna dict {spm: {...}}.
    Curve forza-tempo e forza-posizione mediate (ensemble averaging, cap. 6)."""
    buckets = {}
    for s in strokes:
        spm = s.get("target_spm")
        if not spm:
            continue
        buckets.setdefault(spm, []).append(s)

    out = {}
    for spm, group in buckets.items():
        if len(group) < min_strokes:
            continue
        # curve forza-tempo normalizzate per fase (gia' calcolate come ft_curve)
        ft = [g["ft_curve"] for g in group if g.get("ft_curve") is not None]
        fp = [g["fp_curve"] for g in group if g.get("fp_curve") is not None]
        ft_mean = np.mean(ft, axis=0).round(2).tolist() if ft else None
        fp_mean = np.mean(fp, axis=0).round(2).tolist() if fp else None

        m = {
            "n_strokes": len(group),
            "f_peak_kg": _round(_median([g["f_peak_kg"] for g in group]), 1),
            "f_peak_n": _round(_median([g["f_peak_n"] for g in group]), 0),
            "f_mean_kg": _round(_median([g["f_mean_kg"] for g in group]), 1),
            "impulse_ns": _round(_median([g["impulse_ns"] for g in group]), 1),
            "fullness": _round(_median([g["fullness"] for g in group]), 3),
            "peak_pos": _round(_median([g["peak_pos"] for g in group]), 3),
            "peak_pos_xpct": _round(_median([g["peak_pos_xpct"] for g in group]), 3),
            "rfd_ns": _round(_median([g["rfd_ns"] for g in group]), 0),
            "t_drive_s": _round(_median([g["t_drive_s"] for g in group]), 3),
            "dr_ratio": _round(_median([g["dr_ratio"] for g in group]), 3),
            "drive_length_m": _round(_median([g["drive_length_m"] for g in group]), 3),
            "catch_factor_ms": _round(_median([g["catch_factor_ms"] for g in group]), 1),
            "rsf": _round(_median([g["rsf"] for g in group]), 3),
            "ft_curve": ft_mean,
            "fp_curve": fp_mean,
        }
        # fullness fisicamente implausibile => scarta (artefatto segmentazione)
        if m["fullness"] is not None and m["fullness"] > FULLNESS_MAX_PHYS:
            m["fullness"] = None
        m["assessment"] = assess(m, coordination_calibrated)
        out[str(spm)] = m
    return out


def _round(v, nd):
    return round(v, nd) if v is not None else None


# ─────────────────────────────────────────────────────────────────────────────
# GIUDIZIO E COACHING (bande del documento)
# ─────────────────────────────────────────────────────────────────────────────
def assess(m, coordination_calibrated=False):
    """Ritorna {metric: {grade, cue}} + un cue prioritario, dalle bande del documento.
    Ordine di priorita' d'intervento (cap. 6): 1) connessione al catch (CF, RSF);
    2) fullness/smoothness; 3) lunghezza efficace (slip/wash); 4) sequenza.

    coordination_calibrated=False (default per questo hardware): il Catch Factor a
    risoluzione-ms richiede clock sincronizzati fra encoder e ToF (Fase-1 del
    documento: ritardo sync <5 ms). Finche' l'offset fra i canali non e' calibrato,
    NON si alza l'allarme "shooting the slide" (sarebbe un artefatto): CF e RSF si
    mostrano come informativi/sperimentali, il coaching primario resta su forza e
    posizione (metriche timing-immuni)."""
    a = {}

    cf = m.get("catch_factor_ms")
    if cf is not None and not coordination_calibrated:
        a["catch_factor"] = {"grade": "sperimentale",
            "cue": f"Catch Factor {cf:.0f} ms (sperimentale): il timing sedile↔manubrio non e' "
                   "ancora calibrato fra i due sensori, quindi il valore assoluto non e' "
                   "affidabile — utile solo come trend fra sessioni identiche."}
        cf = None   # non entrare nella logica di allarme sotto

    if cf is not None:
        if cf < CF_SHOOT_MS:
            a["catch_factor"] = {"grade": "da_migliorare",
                "cue": f"Slitta che scappa (Catch Factor {cf:.0f} ms < −50). Le gambe partono a vuoto: "
                       "frena il sellino al catch e collega subito il manubrio."}
        elif cf > CF_POS_GRAB_MS:
            a["catch_factor"] = {"grade": "da_migliorare",
                "cue": f"Manubrio in ritardo sul sellino ({cf:.0f} ms): apri/strappi troppo presto. "
                       "Inverti la direzione attaccando, non aspettare di essere fermo."}
        elif cf <= 0:
            a["catch_factor"] = {"grade": "ottimo",
                "cue": f"Timing al catch eccellente ({cf:.0f} ms): il sellino pre-accelera la massa "
                       "appena prima del manubrio, come i migliori vogatori."}
        else:
            a["catch_factor"] = {"grade": "buono",
                "cue": f"Timing al catch buono ({cf:.0f} ms), leggermente positivo. "
                       "Cerca il sellino appena prima del manubrio (−15 ms ideale)."}

    rsf = m.get("rsf")
    if rsf is not None and not coordination_calibrated:
        a["rsf"] = {"grade": "sperimentale",
            "cue": f"Rowing Style Factor {rsf*100:.0f}% (sperimentale): rapporto corsa sellino/manubrio "
                   "nel primo 20% del drive. Richiede corda e sellino calibrati sullo stesso "
                   "riferimento — per ora indicativo."}
        rsf = None

    if rsf is not None:
        if rsf > RSF_SHOVE:
            a["rsf"] = {"grade": "da_migliorare",
                "cue": f"Bum-shoving (RSF {rsf*100:.0f}% > 100%): il sellino corre piu' del manubrio nel "
                       "primo 20% del drive. Sposta il manubrio insieme alle gambe."}
        elif rsf < RSF_GRAB:
            a["rsf"] = {"grade": "buono",
                "cue": f"RSF {rsf*100:.0f}% (<80%): tendenza a 'grabbing' con tronco/braccia. "
                       "Lascia guidare le gambe."}
        else:
            a["rsf"] = {"grade": "ottimo",
                "cue": f"Sequenza gambe→tronco corretta (RSF {rsf*100:.0f}%, target ~90%)."}

    full = m.get("fullness")
    if full is not None:
        g = _grade(full, FULLNESS_LOW, FULLNESS_HIGH)
        if full < FULLNESS_LOW - 0.02:
            cue = f"Curva 'a spillo' (fullness {full:.2f}, target 0.50–0.65): non mollare dopo il colpo "
            cue += "iniziale, mantieni la pressione per tutto il drive."
        elif full > FULLNESS_HIGH:
            cue = f"Curva molto piena (fullness {full:.2f}): stile simultaneo/plateau, ottimo per potenza "
            cue += "ma verifica la lunghezza."
        else:
            cue = f"Fullness {full:.2f} nella banda elite (0.50–0.65): buona connessione per tutto il drive."
        a["fullness"] = {"grade": g, "cue": cue}

    pp = m.get("peak_pos")
    if pp is not None:
        g = _grade(pp, PEAK_POS_LOW, PEAK_POS_HIGH)
        if pp > PEAK_POS_HIGH + 0.02:
            cue = f"Picco tardivo ({pp*100:.0f}% del drive, ideale 32–40%): carica il peso prima, "
            cue += "aggancia la pedana subito all'attacco."
        elif pp < PEAK_POS_LOW - 0.02:
            cue = f"Picco molto anticipato ({pp*100:.0f}%): curva front-loaded, rischio di 'kick' iniziale "
            cue += "senza aggiunta di tronco/braccia."
        else:
            cue = f"Picco al {pp*100:.0f}% del drive: posizione ideale (massima spinta a gambe piegate)."
        a["peak_pos"] = {"grade": g, "cue": cue}

    dr = m.get("dr_ratio")
    if dr is not None:
        a["dr_ratio"] = {"grade": _grade(dr, DR_LOW, DR_HIGH),
            "cue": f"Rapporto drive:recupero {dr:.2f}" + (
                " — recupero troppo corto, rallenta il ritorno (ideale ~1:2)." if dr > DR_HIGH
                else " nel range corretto (recupero piu' lungo del drive)." )}

    # cue prioritario secondo l'ordine del documento
    priority = None
    for key in ("catch_factor", "rsf", "fullness", "peak_pos"):
        if key in a and a[key]["grade"] == "da_migliorare":
            priority = a[key]["cue"]
            break
    if priority is None:
        # nessun difetto grave: elogia il punto migliore disponibile
        if "catch_factor" in a and a["catch_factor"]["grade"] == "ottimo":
            priority = a["catch_factor"]["cue"]
        elif "fullness" in a:
            priority = a["fullness"]["cue"]
        elif "peak_pos" in a:
            priority = a["peak_pos"]["cue"]
        else:
            priority = "Dati di forza validi: curva coerente per questo bucket di cadenza."

    a["priority_cue"] = priority
    return a


# ─────────────────────────────────────────────────────────────────────────────
# API DI ALTO LIVELLO
# ─────────────────────────────────────────────────────────────────────────────
def analyze(df, seg_threshold, quality, force_col="real_force"):
    """Analizza un'intera sessione (DataFrame gia' calibrato dal parser).
    quality = dict con almeno cord_pos_alive, seat_pos_alive, sampling_1hz_bug.
    Ritorna dict serializzabile con by_spm, session (mediane globali) e disponibilita'."""
    f = df[force_col].values.astype(float)
    t = (df["time_ms"].values / 1000.0).astype(float)
    cord = df["cord_pos"].values.astype(float) if "cord_pos" in df else None
    seat = df["seat_pos"].values.astype(float) if "seat_pos" in df else None
    tspm = df["target_spm"].values if "target_spm" in df else np.zeros(len(df))

    catches, _ = detect_catches(f, seg_threshold)

    # ── Disponibilita' dei segnali di POSIZIONE derivata dal DRIVE, non dal segnale
    # globale. Un canale corda puo' essere sporco nel recupero (valori fuori scala) ma
    # pulito durante il drive: cio' che conta per drive-length/velocita'/coordinazione
    # e' la corsa DENTRO la trazione definita dalla forza. Cosi' non si perde una
    # sessione con 3 segnali validi solo per glitch fuori dal drive.  (cap. 6/Caveats)
    hard_dead = quality.get("sampling_1hz_bug", False)

    def _drive_spans(sig):
        spans = []
        for i in range(len(catches) - 1):
            s, e = max(0, catches[i] - 5), catches[i + 1] - 5
            if e - s < 10:
                continue
            seg_f = f[s:e]
            dm = np.where(seg_f > seg_threshold)[0]
            if len(dm) < 4:
                continue
            seg = sig[s:e][dm[0]:dm[-1] + 1]
            spans.append(float(seg.max() - seg.min()))
        return np.array(spans) if spans else np.array([])

    cord_alive = False
    if cord is not None and not hard_dead and (cord.max() - cord.min()) > 0.1:
        cs = _drive_spans(cord)
        cord_alive = len(cs) >= 10 and 0.3 <= float(np.median(cs)) <= 1.6

    seat_alive = False
    if seat is not None and not hard_dead and (seat.max() - seat.min()) > 0.02:
        ss = _drive_spans(seat)
        # esclude il canale rotto (corse metriche, >0.8 m) e il canale morto (<0.04 m)
        seat_alive = len(ss) >= 10 and 0.04 <= float(np.median(ss)) <= 0.80

    strokes = []
    for i in range(len(catches) - 1):
        s = max(0, catches[i] - 5)
        e = catches[i + 1] - 5
        if e - s < 10:
            continue
        m = stroke_metrics(f[s:e], cord[s:e] if cord is not None else None,
                           seat[s:e] if seat is not None else None, t[s:e],
                           seg_threshold, cord_alive, seat_alive)
        if m is None:
            continue
        # curva forza-tempo normalizzata per fase per l'ensemble
        drive = np.where(f[s:e] > seg_threshold)[0]
        if len(drive) >= 4:
            seg = f[s:e][drive[0]:drive[-1] + 1]
            m["ft_curve"] = _resample_phase(seg, N_CURVE).round(2).tolist()
        else:
            m["ft_curve"] = None
        m["target_spm"] = int(tspm[catches[i]]) if catches[i] < len(tspm) else 0
        strokes.append(m)

    # Calibrazione della coordinazione: il timing sedile↔manubrio a risoluzione ms
    # richiede clock sincronizzati (Fase-1 del documento). Su questo hardware i due
    # canali non sono ancora sincronizzati, quindi Catch Factor/RSF restano
    # sperimentali. Il flag e' pronto per essere alzato quando il FW loggera' i tre
    # canali sullo stesso clock con offset caratterizzato (< 5 ms).
    coordination_calibrated = False

    by_spm = ensemble_by_spm(strokes, coordination_calibrated=coordination_calibrated)

    # metriche globali di sessione (mediane su tutte le vogate valide)
    session = {}
    if strokes:
        session = {
            "n_strokes": len(strokes),
            "fullness": _round(_median([s["fullness"] for s in strokes]), 3),
            "peak_pos": _round(_median([s["peak_pos"] for s in strokes]), 3),
            "peak_pos_xpct": _round(_median([s["peak_pos_xpct"] for s in strokes]), 3),
            "rfd_ns": _round(_median([s["rfd_ns"] for s in strokes]), 0),
            "f_peak_n": _round(_median([s["f_peak_n"] for s in strokes]), 0),
            "impulse_ns": _round(_median([s["impulse_ns"] for s in strokes]), 1),
            "drive_length_m": _round(_median([s["drive_length_m"] for s in strokes]), 3),
            "catch_factor_ms": _round(_median([s["catch_factor_ms"] for s in strokes]), 1),
            "rsf": _round(_median([s["rsf"] for s in strokes]), 3),
            "dr_ratio": _round(_median([s["dr_ratio"] for s in strokes]), 3),
        }
        if session["fullness"] and session["fullness"] > FULLNESS_MAX_PHYS:
            session["fullness"] = None
        session["assessment"] = assess(session, coordination_calibrated)

    return {
        "availability": {
            "force": True,
            "position": cord_alive,       # curva forza-posizione, velocita', slip/wash
            "coordination": cord_alive and seat_alive,   # catch factor, RSF, sequenza
            "coordination_calibrated": coordination_calibrated,
        },
        "reference": {
            "fullness": [FULLNESS_LOW, FULLNESS_HIGH],
            "peak_pos": [PEAK_POS_LOW, PEAK_POS_HIGH],
            "catch_factor_ms": [CF_SHOOT_MS, 0.0],
            "catch_factor_opt": CF_OPT_SCULL_MS,
            "rsf": [RSF_GRAB, RSF_SHOVE],
            "rsf_opt": RSF_OPT,
            "dr_ratio": [DR_LOW, DR_HIGH],
        },
        "session": session,
        "by_spm": by_spm,
    }
