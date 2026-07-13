# 📊 SmartRower Dashboard

**Il cervello analitico dell'ecosistema [SmartRower Pro](https://github.com/Ste86-sudo/SmartRowerPro): ogni sessione di voga diventa biomeccanica leggibile, trend e consigli da coach.**

![Pipeline](https://img.shields.io/badge/pipeline-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)
![Python](https://img.shields.io/badge/analisi-Python%20%2B%20NumPy%2FSciPy-3776AB?logo=python&logoColor=white)
![Dashboard](https://img.shields.io/badge/frontend-HTML%20statico-e34c26)
![Biomeccanica](https://img.shields.io/badge/metriche-letteratura%20(Kleshnev%2C%20Holt%2C%20Warmenhoven)-8A2BE2)

---

## L'ecosistema in una pagina

**SmartRower Pro** è un vogatore ad aria V-Fit Tornado trasformato in ergometro strumentato DIY: cella di carico 24-bit sulla maniglia, encoder sulla corda, laser ToF sul sellino, fascia cardio BLE, due ESP32-S3 collegati via ESP-NOW. Il firmware campiona **tre segnali a 100 Hz** — forza, posizione manubrio, posizione sellino — e serve una web UI offline con coach in tempo reale e **ghost curves** fisiche.

Questa repo è il pezzo che vive *dopo* l'allenamento:

```
🚣 Vogata sul Tornado
      │  export CSV dalla web UI (3 segnali @ 100 Hz)
      ▼
📥 smartrower_downloads/          ← basta committare il CSV
      │  GitHub Action (data_pipeline.yml)
      ▼
🐍 smartrower_parser.py + biomechanics.py     🐍 analyzer.py (sessioni EXR via .fit)
      │  segmentazione colpi, metriche, giudizi, cue
      ▼
📄 smartrower_data.js / data.js / processed_sessions.json
      │
      ▼
📈 index.html — la dashboard: trend, sessioni, curve di forza, coach
```

Tutto automatico: si carica un CSV, la Action rigenera i dati, la dashboard si aggiorna.

---

## La biomeccanica: metriche guidate dalla letteratura

Il motore [`biomechanics.py`](biomechanics.py) non inventa soglie: implementa le bande di riferimento della letteratura del canottaggio (Kleshnev/Biorow, Holt et al. 2020, Warmenhoven et al. 2017-18, Dudhia) e per ogni metrica restituisce **valore + banda di riferimento + giudizio graduato + cue di coaching**:

| Metrica | Banda di riferimento | Cosa smaschera |
|---|---|---|
| **Fullness** (F media/F picco) | 0.50–0.65 | curva "a spillo" = connessione persa |
| **Posizione del picco** | 32–40% del drive | picco tardivo = sforzo sprecato |
| **Catch factor** | −15/−25 ms (sellino prima del manubrio) | < −50 ms = *shooting the slide* |
| **Rowing Style Factor** | ~0.90 sellino:manubrio (primo 20% drive) | > 1.0 = *bum-shoving*, < 0.80 = *grabbing* |
| **Drive:recovery** | ~1:2, cresce con lo SPM | ritorno troppo veloce |

Due scelte di design prese dalla letteratura e applicate ovunque:

1. **Curve ensemble normalizzate per fase** (catch = 0%, finish = 100%, Warmenhoven): vogate di durata diversa restano confrontabili, il campionamento a tempo fisso no.
2. **Filosofia quality-aware**: ogni metrica si calcola *solo* se i segnali che le servono sono vivi e affidabili in quella sessione. La forza c'è quasi sempre; corda e sellino spesso no — e la dashboard lo dice, invece di mostrare numeri inventati.

I **consigli del coach** ([`coach_advice.js`](coach_advice.js)) seguono la stessa regola del firmware: un difetto → un cue mirato, in italiano, con priorità (prima la sequenza, poi il carico, poi la forma) — non una pagella di dieci voti insieme.

### Le ghost curves

Sul firmware, la curva target non è disegnata a mano: nasce dal modello fisico della macchina (`F = b₂·v²`, aria quasi pura, b₂ ≈ 110 N·s²/m²) e da una cinematica minimum-jerk della sequenza gambe→tronco→braccia. Tre curve accoppiate — forza, sellino, braccia — perché la forza da sola è cieca alla coordinazione. La specifica completa è in [SmartRowerPro/docs](https://github.com/Ste86-sudo/SmartRowerPro/tree/master/docs).

---

## Cosa mostra la dashboard

- **Panoramica**: allenamenti, distanza, potenza, calorie; filtri endurance / HIIT / sprint; banner milestone.
- **Trend**: potenza e distanza nel tempo (grafici canvas).
- **Dettaglio sessione** (modal): curve forza-tempo e **forza-posizione**, potenza, SPM, striscia di qualità dei segnali, metriche biomeccaniche con giudizio e consiglio del coach.
- **Sessioni EXR**: `analyzer.py` scarica e integra anche gli allenamenti fatti su [EXR](https://www.exrgame.com) (file .fit via Playwright).

---

## Uso locale

```bash
pip install pandas numpy scipy fitparse playwright
python smartrower_parser.py     # rigenera smartrower_data.js dai CSV
python -m http.server 8000      # poi apri http://localhost:8000/index.html
```

In CI fa tutto [.github/workflows/data_pipeline.yml](.github/workflows/data_pipeline.yml): si attiva sul push di nuovi file in `smartrower_downloads/` o `downloads/`.

---

## Le repo dell'ecosistema

| Repo | Contenuto |
|---|---|
| **[SmartRowerPro](https://github.com/Ste86-sudo/SmartRowerPro)** | Firmware ESP32 (Telaio + Maniglia), web UI offline con coach live e ghost curves, analizzatore Python con fPCA, simulatore |
| **smartrower-dashboard** (questa) | Pipeline dati post-sessione, motore biomeccanico, dashboard storica |

## 🗺 Prossimi passi

- [ ] 🌐 **Sito vetrina del sistema** (GitHub Pages): la storia del progetto, la fisica, demo interattiva della dashboard
- [ ] Log firmware a 3 canali con seat_pos attivo → sblocco completo delle metriche di coordinazione
- [ ] Pulizia degli script temporanei (`temp_*.py`)

---

*Riferimenti: V. Kleshnev — Biorow (curva di forza, catch factor, RSF); Holt et al. 2020; Warmenhoven et al. 2017-18 (analisi funzionale delle curve); A. Dudhia — Physics of Ergometers.*
