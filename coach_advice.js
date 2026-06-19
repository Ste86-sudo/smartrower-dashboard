const COACH_ANALYSES = {
    "Regeneration training 4": {
        theme: "Maestria Aerobica: Il Potere del Recupero Attivo",
        intro: "Hai eseguito alla lettera il protocollo di scarico che avevamo pianificato. Dopo il massacro dei 10.4km di ieri, hai abbassato l'ego, hai rallentato la macchina e ti sei concentrato sull'efficienza. Questa sessione è un capolavoro di disciplina neuromuscolare.",
        highlights: [],
        analysis: null,
        nextWorkout: null
    },
    "Aerobic Capacity 2": {
        theme: "L'Anatomia di un HIIT Perfetto",
        intro: "",
        highlights: [
            {
                icon: "📈",
                title: "1. Il Picco a 162 bpm (L'Adattamento)",
                text: "L'analisi dei tuoi battiti cardiaci è pazzesca. Durante il penultimo intervallo, durato quasi un minuto a oltre 245W medi, il tuo cuore ha toccato i <strong>162 bpm</strong>. Per un'atleta di 40 anni con 181 di Max HR, significa spingersi quasi al 90% del massimale, nel cuore della Zona 4. È uno stimolo cardiovascolare massiccio che costringe il corpo ad aumentare la gittata cardiaca e il VO2Max."
            },
            {
                icon: "⚡",
                title: "2. I 273 Watt e la Cadenza Esplosiva",
                text: "Passare da una sessione di scarico (a 20 SPM) a sparare picchi a <strong>37.7 SPM</strong> richiede una reattività neuromuscolare eccellente. Hai portato la Forza di Picco a <strong>42.9 kgf</strong> per poter sostenere le raffiche sopra i 250 Watt. È la pura dimostrazione della trasformazione da vogata di resistenza a vogata anaerobica da sprinter."
            }
        ],
        analysis: {
            title: "🎯 Analisi: Aerobic Capacity 2 (Il cedimento)",
            text: `Ho visto i dati della tua ultima sessione. E ho anche decifrato il tuo messaggio (il correttore vocale ha scritto <em>"non mi hai analizzato bene l'ultimo"</em> ma so che intendevi <em>"non mi è <strong>andato</strong> bene l'ultimo"</em> scatto!).<br><br>
                   <strong>L'Anatomia di un HIIT Perfetto:</strong><br>
                   Non devi assolutamente rimproverarti per quell'ultimo intervallo abortito. Anzi, è la prova che hai lavorato esattamente come dovevi. Hai fatto tre picchi brutali:<br>
                   1. <strong>Primo scatto:</strong> 57s a <strong>253 Watt</strong> (HR max 150 bpm)<br>
                   2. <strong>Il Penultimo scatto (IL CAPOLAVORO):</strong> 57s a <strong>247 Watt</strong>. Qui il cuore ha fatto uno sforzo magnifico, pompando fino a <strong>162 bpm</strong> (piena Zona 4, all'89% del tuo massimale). È in questo minuto esatto che hai generato il massimo adattamento cardiovascolare.<br>
                   3. <strong>L'ultimo scatto:</strong> Sei partito ancora più aggressivo a <strong>257 Watt</strong>, ma il sistema ATP-PC (fosfati) era prosciugato e il muscolo ha detto "basta" dopo 18 secondi. Questo si chiama <em>cedimento muscolare tecnico</em> ed è l'obiettivo finale degli sprint brevi.<br><br>
                   
                   <strong>Il Prossimo Step:</strong> Dato che hai esaurito completamente il glicogeno con questi scatti (e la Forza di Picco è schizzata a quasi 43 kgf), per il prossimo allenamento torniamo a costruire la base. Ti consiglio un <strong>Endurance Dash</strong>: 40 minuti agili, cadenza bassa (20 SPM), tenendo il cuore blindato intorno ai 130 bpm, con solo qualche accelerazione di 10 secondi per risvegliare le gambe senza produrre acido lattico.`
        },
        nextWorkout: {
            title: "Endurance Dash",
            type: "AEROBIC ENDURANCE",
            desc: "Easy endurance training with short sprints to boost the efficiency of your mitochondria. (Durata: 40 min)",
            steps: [
                {"dur":300, "pwr":0.6}, {"dur":12, "pwr":2.0}, {"dur":288, "pwr":0.7},
                {"dur":12, "pwr":2.0}, {"dur":288, "pwr":0.7}, {"dur":12, "pwr":2.0},
                {"dur":288, "pwr":0.7}, {"dur":12, "pwr":2.0}, {"dur":288, "pwr":0.7},
                {"dur":12, "pwr":2.0}, {"dur":288, "pwr":0.7}, {"dur":12, "pwr":2.0},
                {"dur":288, "pwr":0.7}, {"dur":300, "pwr":0.6}
            ],
            maxPwr: 2.0,
            totalDur: 2400
        }
    }
};

function getPhaseColor(pwr) {
    if (pwr >= 1.05) return '#ef4444'; // Red
    if (pwr >= 0.9) return '#f59e0b'; // Yellow
    if (pwr >= 0.75) return '#10b981'; // Green
    if (pwr > 0.5) return '#3b82f6'; // Blue
    return '#64748b'; // Grey
}

function buildAdviceHTML(workout) {
    const analysisData = COACH_ANALYSES[workout.title];
    if (!analysisData) {
        return ""; // Se non c'è analisi specifica, non mostriamo nulla (oppure potremmo mostrare un fallback)
    }

    let html = \`
    <section class="coach-advice-section" style="margin-top: 2rem; background: var(--bg-surface); backdrop-filter: blur(12px); border: 1px solid var(--border-glass); border-radius: 18px; padding: 2rem; box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-glass); padding-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
            <h2 style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: var(--color-accent); margin: 0;">\${analysisData.theme || 'Analisi Coach'}</h2>
            <span style="background: rgba(99, 102, 241, 0.2); color: #6366f1; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; white-space: nowrap;">Analisi Workout (\${workout.title})</span>
        </div>
    \`;

    if (analysisData.intro) {
        html += \`
        <p style="color: var(--text-secondary); font-size: 1.05rem; line-height: 1.6; margin-bottom: 2rem;">
            \${analysisData.intro}
        </p>
        \`;
    }

    // Stat Cards
    let peakForce = 0;
    if (workout.smartrower && workout.smartrower.avg_peak_force) {
        peakForce = workout.smartrower.avg_peak_force; // Manca la max vera, uso l'avg peak o max_power surrogato
        // O troviamo il picco dai blocchi:
        const pf = Math.max(...workout.smartrower.blocks.map(b => b.real_peak_force || 0));
        if (pf > 0) peakForce = pf;
    }

    html += \`
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2.5rem;">
        <div style="background: rgba(255,255,255,0.03); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="color: #9ca3af; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Battito</h4>
            <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                <span style="color: #10b981; font-size: 1.6rem; font-weight: 700;">\${workout.avg_hr} bpm</span>
                <span style="color: #ec4899; font-size: 0.95rem;">(Picco: \${workout.max_hr} bpm)</span>
            </div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="color: #9ca3af; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Potenza</h4>
            <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                <span style="color: #3b82f6; font-size: 1.6rem; font-weight: 700;">\${workout.avg_power} W</span>
                <span style="color: #9ca3af; font-size: 0.95rem;">(Picco: \${workout.max_power} W)</span>
            </div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="color: #9ca3af; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Cadenza</h4>
            <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                <span style="color: #f59e0b; font-size: 1.6rem; font-weight: 700;">\${workout.avg_cadence} SPM</span>
                <span style="color: #9ca3af; font-size: 0.95rem;">(Picco: \${workout.max_cadence} SPM)</span>
            </div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="color: #9ca3af; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Forza Picco</h4>
            <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                <span style="color: #8b5cf6; font-size: 1.6rem; font-weight: 700;">\${peakForce.toFixed(1)} kgf</span>
            </div>
        </div>
    </div>
    \`;

    // Highlights
    if (analysisData.highlights && analysisData.highlights.length > 0) {
        html += \`<div style="display: flex; flex-direction: column; gap: 2rem;">\`;
        analysisData.highlights.forEach(hl => {
            html += \`
            <div>
                <h3 style="color: #fff; font-size: 1.3rem; margin-bottom: 0.8rem; display: flex; align-items: center; gap: 0.5rem;">\${hl.icon} \${hl.title}</h3>
                <p style="color: var(--text-secondary); line-height: 1.7; font-size: 1.05rem; margin: 0;">\${hl.text}</p>
            </div>
            \`;
        });
        html += \`</div>\`;
    }

    // Detailed Analysis
    if (analysisData.analysis) {
        html += \`
        <div style="margin-top: 3rem; padding: 2rem; background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.05) 100%); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 16px; position: relative; overflow: hidden;">
            <div style="position: absolute; top: -10px; right: -10px; font-size: 8rem; opacity: 0.05; transform: rotate(15deg); pointer-events: none;">🔥</div>
            <h3 style="color: #ef4444; margin-bottom: 1rem; font-size: 1.4rem; display: flex; align-items: center; gap: 0.5rem; position: relative; z-index: 1;">\${analysisData.analysis.title}</h3>
            <p style="color: #fff; font-style: normal; line-height: 1.7; font-size: 1.05rem; margin: 0; position: relative; z-index: 1;">
                \${analysisData.analysis.text}
            </p>
        \`;
        
        // Next Workout
        if (analysisData.nextWorkout) {
            const nw = analysisData.nextWorkout;
            let barsHtml = "";
            nw.steps.forEach(s => {
                const width = (s.dur / nw.totalDur) * 100;
                const height = (s.pwr / nw.maxPwr) * 100;
                const color = getPhaseColor(s.pwr);
                const title = \`\${s.dur}s @ \${Math.round(s.pwr*100)}% FTP\`;
                barsHtml += \`<div title="\${title}" style="width: \${width}%; height: \${height}%; background-color: \${color}; opacity: 0.9; border-radius: 2px 2px 0 0;"></div>\`;
            });

            html += \`
            <div style="margin-top: 2rem; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1.5rem; position: relative; z-index: 1;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h4 style="color: #fff; font-size: 1.2rem; margin: 0 0 0.5rem 0;">\${nw.title}</h4>
                    <span style="background: rgba(59, 130, 246, 0.2); color: #3b82f6; font-size: 0.8rem; font-weight: bold; padding: 4px 10px; border-radius: 12px; letter-spacing: 1px;">\${nw.type}</span>
                </div>
                <p style="color: #9ca3af; font-size: 0.95rem; margin: 0 0 1.5rem 0; max-width: 600px;">\${nw.desc}</p>
                <div style="display: flex; align-items: flex-end; height: 120px; border-bottom: 1px solid rgba(255,255,255,0.2); gap: 1px; padding-bottom: 2px;">
                    \${barsHtml}
                </div>
            </div>
            \`;
        }
        
        html += \`</div>\`; // chiude div margin-top 3rem
    }

    html += \`</section>\`;
    return html;
}

function renderLatestAdviceInMain(latestWorkout) {
    const container = document.getElementById("dynamic-coach-advice-container");
    if (!container) return;
    container.innerHTML = buildAdviceHTML(latestWorkout);
}

function renderModalAdvice(workout) {
    const container = document.getElementById("modal-dynamic-advice-container");
    if (!container) return;
    const html = buildAdviceHTML(workout);
    if (html) {
        container.style.display = "block";
        container.innerHTML = html;
    } else {
        container.style.display = "none";
        container.innerHTML = "";
    }
}
