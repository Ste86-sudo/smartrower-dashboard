# 📊 SmartRower Dashboard

**The analytics brain of the [SmartRower Pro](https://github.com/Ste86-sudo/SmartRowerPro) ecosystem: every rowing session becomes readable biomechanics, trends and coach advice.**

![Pipeline](https://img.shields.io/badge/pipeline-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)
![Python](https://img.shields.io/badge/analysis-Python%20%2B%20NumPy%2FSciPy-3776AB?logo=python&logoColor=white)
![Dashboard](https://img.shields.io/badge/frontend-static%20HTML-e34c26)
![Biomechanics](https://img.shields.io/badge/metrics-literature%20(Kleshnev%2C%20Holt%2C%20Warmenhoven)-8A2BE2)

---

## The ecosystem in one page

**SmartRower Pro** is a V-Fit Tornado air rower turned into a DIY instrumented ergometer: a 24-bit load cell on the handle, a cord encoder, a ToF laser on the seat, a BLE heart-rate strap, two ESP32-S3 boards linked over ESP-NOW. The firmware samples **three signals at 100 Hz** — force, handle position, seat position — and serves an offline web UI with a real-time coach and physics-generated **ghost curves**. Live demo: [smartrowerpro.com](https://smartrowerpro.com).

This repo is the part that lives *after* the workout:

```
🚣 Row on the Tornado
      │  CSV export from the web UI (3 signals @ 100 Hz)
      ▼
📥 smartrower_downloads/          ← just commit the CSV
      │  GitHub Action (data_pipeline.yml)
      ▼
🐍 smartrower_parser.py + biomechanics.py     🐍 analyzer.py (EXR sessions via .fit)
      │  stroke segmentation, metrics, graded judgments, cues
      ▼
📄 smartrower_data.js / data.js / processed_sessions.json
      │
      ▼
📈 index.html — the dashboard: trends, sessions, force curves, coach
```

Fully automatic: push a CSV, the Action regenerates the data, the dashboard updates.

---

## Biomechanics guided by the literature

The engine in [`biomechanics.py`](biomechanics.py) does not invent thresholds: it implements the reference bands published in rowing biomechanics research (Kleshnev/Biorow, Holt et al. 2020, Warmenhoven et al. 2017-18, Dudhia). Every metric returns **value + reference band + graded judgment + a targeted coaching cue**:

| Metric | Reference band | What it unmasks |
|---|---|---|
| **Fullness** (F_mean/F_peak) | 0.50–0.65 | spiky curve = lost connection |
| **Peak position** | 32–40 % of drive | late effort |
| **Catch factor** | −15/−25 ms (seat before handle) | < −50 ms = *shooting the slide* |
| **Rowing Style Factor** | ≈ 0.90 seat:handle (first 20 % of drive) | > 1.0 *bum-shoving*, < 0.80 *grabbing* |
| **Drive:recovery** | ≈ 1:2, grows with SPM | rushed recovery |

Two design choices taken straight from the literature:

1. **Phase-normalised ensemble curves** (catch = 0 %, finish = 100 %, Warmenhoven): strokes of different duration stay comparable — fixed-time sampling does not.
2. **Quality-aware philosophy**: each metric is computed *only* if the signals it needs are alive and reliable in that session. Force almost always is; cord and seat often are not — and the dashboard says so instead of showing invented numbers.

The coach advice ([`coach_advice.js`](coach_advice.js)) follows the same rule as the firmware: one fault → one targeted cue, priority-ordered (sequence, then loading, then shape).

---

## What the dashboard shows

- **Overview**: workouts, distance, power, calories; endurance / HIIT / sprint filters; milestone banner.
- **Trends**: power and distance over time (canvas charts).
- **Session detail** (modal): force-time and **force-position** curves, power, SPM, signal-quality strip, biomechanics metrics with judgment and coach advice.
- **EXR sessions**: `analyzer.py` also ingests workouts rowed on [EXR](https://www.exrgame.com) (.fit files via Playwright).

## Local use

```bash
pip install pandas numpy scipy fitparse playwright
python smartrower_parser.py     # regenerate smartrower_data.js from the CSVs
python -m http.server 8000      # then open http://localhost:8000/index.html
```

CI does all of this in [.github/workflows/data_pipeline.yml](.github/workflows/data_pipeline.yml), triggered by pushes to `smartrower_downloads/` or `downloads/`.

## The ecosystem repos

| Repo | Content |
|---|---|
| **[SmartRowerPro](https://github.com/Ste86-sudo/SmartRowerPro)** | ESP32 firmware (frame + handle), offline web UI with live coach and ghost curves, Python analyzer with fPCA, simulator, 153 workouts + 4 training plans |
| **smartrower-dashboard** (this one) | Post-session data pipeline, biomechanics engine, historical dashboard |

## Next steps

- [ ] Firmware 3-channel logging with seat_pos active → full coordination metrics
- [ ] Clean up temporary scripts (`temp_*.py`)

---

*References: V. Kleshnev — Biorow (force curve, catch factor, RSF); Holt et al. 2020; Warmenhoven et al. 2017-18 (functional analysis of force curves); A. Dudhia — The Physics of Ergometers. Full bibliography: [smartrowerpro.com/#refs](https://smartrowerpro.com/#refs).*
