import os
import json
import time
import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
import fitparse

# Define paths
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DB_FILE = BASE_DIR / "processed_sessions.json"
DATA_JS_FILE = BASE_DIR / "data.js"
HTML_DUMP_FILE = BASE_DIR / "sessions_page.html"
USER_DATA_DIR = BASE_DIR / "browser_session"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"

# Ensure directories exist
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_processed_sessions():
    if DB_FILE.exists():
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_processed_sessions(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def update_data_js(processed):
    """
    Exports workout data to data.js as a global variable, sorted with the most recent at the top.
    """
    try:
        sessions_list = list(processed.values())
        # Sort by date descending (most recent first)
        sessions_list.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        js_content = f"const WORKOUT_DATA = {json.dumps(sessions_list, indent=4, ensure_ascii=False)};"
        with open(DATA_JS_FILE, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(f"File data.js aggiornato con successo in: {DATA_JS_FILE}")
    except Exception as e:
        print(f"Errore durante l'aggiornamento di data.js: {e}")

def load_credentials():
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def downsample_list(lst, num_points=50):
    """
    Evenly samples num_points from a list to keep the data size extremely compact.
    """
    if not lst:
        return []
    if len(lst) <= num_points:
        return lst
    sampled = []
    for i in range(num_points):
        idx = int(i * (len(lst) - 1) / (num_points - 1))
        sampled.append(lst[idx])
    return sampled

def parse_fit_file(filepath):
    """
    Parses a FIT file using fitparse and returns a dictionary of workout metrics.
    """
    try:
        fitfile = fitparse.FitFile(str(filepath))
    except Exception as e:
        print(f"Errore durante l'apertura del file FIT {filepath}: {e}")
        return None

    session_msg = None
    for msg in fitfile.get_messages('session'):
        session_msg = msg
        break

    records = []
    for msg in fitfile.get_messages('record'):
        record_data = {}
        for field in msg:
            record_data[field.name] = field.value
        if record_data.get('power') is not None and record_data['power'] > 700:
            record_data['power'] = None
        records.append(record_data)

    metrics = {}
    if session_msg:
        for field in session_msg:
            metrics[field.name] = field.value
    
    if not metrics.get('start_time') and records:
        metrics['start_time'] = records[0].get('timestamp')
        
    if not metrics.get('total_elapsed_time') and records:
        start = records[0].get('timestamp')
        end = records[-1].get('timestamp')
        if start and end:
            metrics['total_elapsed_time'] = (end - start).total_seconds()

    if not metrics.get('total_timer_time') and metrics.get('total_elapsed_time'):
        metrics['total_timer_time'] = metrics['total_elapsed_time']

    summary = {
        "filename": filepath.name,
        "date": None,
        "duration_min": 0,
        "distance_m": 0,
        "calories": 0,
        "avg_power": 0,
        "max_power": 0,
        "avg_hr": 0,
        "max_hr": 0,
        "avg_cadence": 0,
        "max_cadence": 0,
        "raw_metrics": {}
    }

    start_time = metrics.get('start_time')
    if isinstance(start_time, datetime.datetime):
        summary["date"] = start_time.strftime("%Y-%m-%d %H:%M:%S")
    elif start_time:
        summary["date"] = str(start_time)
    else:
        stat = filepath.stat()
        summary["date"] = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    timer_time = metrics.get('total_timer_time') or metrics.get('total_elapsed_time')
    if timer_time:
        summary["duration_min"] = round(timer_time / 60.0, 1)

    dist = metrics.get('total_distance')
    if dist is not None:
        summary["distance_m"] = round(dist, 1)
    elif records:
        last_dist = records[-1].get('distance')
        if last_dist is not None:
            summary["distance_m"] = round(last_dist, 1)

    cals = metrics.get('total_calories') or metrics.get('total_total_calories')
    if cals is not None:
        summary["calories"] = int(cals)

    avg_p = metrics.get('avg_power')
    max_p = metrics.get('max_power')
    if avg_p is not None:
        summary["avg_power"] = round(avg_p, 1)
    elif records:
        p_vals = [r['power'] for r in records if r.get('power') is not None]
        if p_vals:
            summary["avg_power"] = round(sum(p_vals) / len(p_vals), 1)
            
    if max_p is not None and max_p <= 700:
        summary["max_power"] = round(max_p, 1)
    elif records:
        p_vals = [r['power'] for r in records if r.get('power') is not None]
        if p_vals:
            summary["max_power"] = max(p_vals)

    avg_h = metrics.get('avg_heart_rate')
    max_h = metrics.get('max_heart_rate')
    if avg_h is not None:
        summary["avg_hr"] = int(avg_h)
    elif records:
        h_vals = [r['heart_rate'] for r in records if r.get('heart_rate') is not None]
        if h_vals:
            summary["avg_hr"] = int(sum(h_vals) / len(h_vals))

    if max_h is not None:
        summary["max_hr"] = int(max_h)
    elif records:
        h_vals = [r['heart_rate'] for r in records if r.get('heart_rate') is not None]
        if h_vals:
            summary["max_hr"] = max(h_vals)

    avg_c = metrics.get('avg_cadence') or metrics.get('avg_stroke_rate')
    max_c = metrics.get('max_cadence') or metrics.get('max_stroke_rate')
    if avg_c is not None:
        summary["avg_cadence"] = round(avg_c, 1)
    elif records:
        c_vals = [r['cadence'] for r in records if r.get('cadence') is not None]
        if c_vals:
            summary["avg_cadence"] = round(sum(c_vals) / len(c_vals), 1)

    if max_c is not None:
        summary["max_cadence"] = round(max_c, 1)
    elif records:
        c_vals = [r['cadence'] for r in records if r.get('cadence') is not None]
        if c_vals:
            summary["max_cadence"] = max(c_vals)

    for k, v in metrics.items():
        if isinstance(v, (int, float, str)):
            summary["raw_metrics"][k] = v

    # Extract second-by-second power and downsample to 50 points
    power_series = [r.get('power') for r in records if r.get('power') is not None]
    summary["power_series"] = downsample_list(power_series, 50)

    return summary

def download_and_analyze_sessions(headless=False):
    processed = load_processed_sessions()
    credentials = load_credentials()
    
    # Backfill missing power_series for older processed sessions from local downloads
    changed = False
    for session_id, summary in processed.items():
        if "power_series" not in summary:
            filename = summary.get("filename")
            if filename:
                filepath = DOWNLOADS_DIR / filename
                if filepath.exists():
                    print(f"Retro-estrazione 'power_series' per sessione {session_id} da {filename}...")
                    full_summary = parse_fit_file(filepath)
                    if full_summary and "power_series" in full_summary:
                        summary["power_series"] = full_summary["power_series"]
                        changed = True
    if changed:
        save_processed_sessions(processed)
        print("Database locale aggiornato con le serie temporali retroattive.")
    
    # Proactively update data.js on launch
    update_data_js(processed)
    
    print(f"Avvio di Playwright con sessione persistente (headless={headless})...")
    new_downloads = []

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=headless
        )
        page = context.new_page()

        print("\n=== AZIONE RICHIESTA ===")
        print("Ho aperto una finestra del browser.")
        if credentials:
            print("Credenziali trovate! Proverò ad effettuare l'autologin se necessario.")
        else:
            print("Per abilitare l'autologin, inserisci le credenziali EXR nel file credentials.json.")
        print("========================")

        page.goto("https://account.exrgame.com/sessions")

        max_wait_login_s = 300
        start_wait = time.time()
        logged_in = False
        last_printed_url = ""
        autologin_attempted = False
        
        while time.time() - start_wait < max_wait_login_s:
            current_url = page.url
            if current_url != last_printed_url:
                print(f"URL corrente del browser: {current_url}")
                last_printed_url = current_url

            # Autologin logic
            if "/login" in current_url and credentials and not autologin_attempted:
                print("Rilevata pagina di login. Avvio autologin...")
                try:
                    try:
                        page.click("button.js-cookie-consent-agree", timeout=3000)
                        print("Cookie accettati con successo.")
                    except Exception:
                        pass
                    
                    page.fill("input#form-email", credentials["email"])
                    page.fill("input#form-password", credentials["password"])
                    print("Credenziali inserite. Clicco su Log in...")
                    page.click("button[type='submit']")
                    autologin_attempted = True
                    time.sleep(3)
                    continue
                except Exception as e:
                    print(f"Errore durante l'autologin: {e}")

            # Auto-redirect to sessions if the user lands on other profile/dashboard pages
            if "account.exrgame.com" in current_url:
                if "/login" not in current_url and "/sessions" not in current_url:
                    print("Utente loggato rilevato in un'altra pagina. Reindirizzamento a /sessions...")
                    page.goto("https://account.exrgame.com/sessions")
                    time.sleep(2)
                    continue

            if "account.exrgame.com/sessions" in current_url:
                print("Pagina delle sessioni rilevata correttamente!")
                logged_in = True
                break
                
            time.sleep(1)

        if not logged_in:
            print("Timeout scaduto. Non è stata raggiunta la pagina delle sessioni.")
            context.close()
            return []

        print("Attesa del caricamento completo della pagina delle sessioni...")
        time.sleep(5)

        html_content = page.content()
        with open(HTML_DUMP_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Dump HTML salvato in: {HTML_DUMP_FILE}")

        # Scan for download links specifically matching session fit downloads
        links = page.locator("a[href*='/sessions/download/fit/']").all()
        download_targets = []

        print(f"Rilevati {len(links)} link di download sessione dedicati.")

        for idx, link in enumerate(links):
            try:
                href = link.get_attribute("href") or ""
                text = link.inner_text() or ""
                download_targets.append({
                    "index": idx,
                    "href": href,
                    "text": text.strip(),
                    "locator": link
                })
            except Exception:
                continue

        downloaded_count = 0
        for target in download_targets:
            href = target["href"]
            text = target["text"]
            locator = target["locator"]

            # Extract the UUID as the session_id
            session_id = href.split("/")[-1]

            if session_id in processed:
                continue

            print(f"Trovata NUOVA sessione! ID: {session_id}. Inizio download...")
            
            try:
                locator.scroll_into_view_if_needed()
                
                with page.expect_download(timeout=30000) as download_info:
                    locator.click()
                
                download = download_info.value
                filename = download.suggested_filename
                
                if not filename.endswith(".fit") and not filename.endswith(".tcx") and not filename.endswith(".gpx"):
                    filename += ".fit"

                filepath = DOWNLOADS_DIR / filename
                download.save_as(str(filepath))
                print(f"Scaricato con successo: {filename}")

                summary = parse_fit_file(filepath)
                if summary:
                    summary["session_id"] = session_id
                    processed[session_id] = summary
                    new_downloads.append(summary)
                    downloaded_count += 1
                else:
                    print(f"Impossibile analizzare il file scaricato per la sessione {session_id}")

            except Exception as e:
                print(f"Errore durante il download o l'analisi della sessione {session_id}: {e}")

        # Save and sync JS
        save_processed_sessions(processed)
        update_data_js(processed)
        print(f"\nOperazione completata. Nuove sessioni scaricate ed elaborate: {downloaded_count}")

        context.close()

    return new_downloads

if __name__ == "__main__":
    import sys
    
    # Check if we should only run once a day
    if "--daily" in sys.argv:
        last_run_file = BASE_DIR / "last_run_date.txt"
        today_str = datetime.date.today().isoformat()
        if last_run_file.exists():
            try:
                with open(last_run_file, "r", encoding="utf-8") as f:
                    last_date = f.read().strip()
                if last_date == today_str:
                    print("EXR Analyzer ha già eseguito l'aggiornamento quotidiano oggi.")
                    sys.exit(2)
            except Exception:
                pass
                
        # First run of the day: record today's date
        try:
            with open(last_run_file, "w", encoding="utf-8") as f:
                f.write(today_str)
        except Exception as e:
            print(f"Impossibile salvare la data dell'ultimo aggiornamento: {e}")

    headless_mode = "--headless" in sys.argv
    results = download_and_analyze_sessions(headless=headless_mode)
    if results:
        print("\n--- RISULTATI DELLE NUOVE SESSIONI ---")
        for res in results:
            print(f"\nData Sessione: {res['date']}")
            print(f"  File: {res['filename']}")
            print(f"  Durata: {res['duration_min']} min")
            print(f"  Distanza: {res['distance_m']} m")
            print(f"  Calorie: {res['calories']} kcal")
            print(f"  Potenza Media: {res['avg_power']} W (Max: {res['max_power']} W)")
            print(f"  BPM Medio: {res['avg_hr']} bpm (Max: {res['max_hr']} bpm)")
            print(f"  Cadenza Media: {res['avg_cadence']} spm (Max: {res['max_cadence']} spm)")
    else:
        print("\nNessuna nuova sessione trovata o scaricata.")
