const COACH_ANALYSES = {
    "Long VO2max Intervals 2": {
        theme: "🫀 Sofferenza Pura: Il Muro del Lattato",
        intro: "Questa è la definizione da manuale di un allenamento per il VO2Max. Hai alternato blocchi ad altissima intensità a recuperi in zona aerobica, portando il sistema cardiovascolare all'esasperazione.",
        highlights: [
            {
                icon: "🚀",
                title: "1. Le Sfuriate a 275 Watt",
                text: "Hai aperto le danze con due blocchi da 1 minuto a quasi <strong>275W</strong>. È una potenza paurosa. In questa fase il tuo sistema ha bruciato fosfati e glicogeno come se non ci fosse un domani, attivando in pieno le fibre veloci."
            },
            {
                icon: "📈",
                title: "2. La Deriva Cardiaca in Diretta",
                text: "Nei blocchi successivi (1 minuto a 300W target), la potenza è fisiologicamente e leggermente calata (<strong>272W -> 255W -> 251W</strong>), ma guarda i battiti: <strong>141 -> 157 -> 161 -> 167 bpm</strong>! A parità di sforzo (anzi, perfino con watt inferiori), il tuo cuore ha dovuto battere sempre più forte per sopperire alla mancanza di ossigeno e allo smaltimento dell'acido lattico. È la prova che il VO2Max è stato stimolato al 100%."
            }
        ],
        analysis: {
            title: "🧬 Analisi: Long VO2max Intervals 2 (Il debito d'ossigeno)",
            text: \`Un allenamento del genere crea un debito d'ossigeno enorme. I 12 secondi a 400W target (chiusi a ~265W) sono serviti come "innesco" neuromuscolare per preparare il sistema nervoso centrale, ma il vero lavoro lo hai fatto nei blocchi da 1 minuto.<br><br>
                   Non farti frustrare dal fatto che nei blocchi da 300W non hai tenuto i 300W, ma sei sceso a 251W. Per la tua fisiologia attuale, 270W è già uno stimolo supramassimale. Il fatto che tu abbia tenuto i 180-190W di media nei blocchi di "recupero" da 3 minuti è ammirevole e dimostra un'eccellente capacità di clearing del lattato.<br><br>
                   <strong>Il Prossimo Step:</strong> Questo allenamento richiede almeno 48h di recupero muscolare. Il prossimo deve essere un fondo lungo a bassissima intensità per favorire la capillarizzazione.\`
        },
        nextWorkout: {
            title: "Base Aerobica",
            type: "AEROBIC ENDURANCE",
            desc: "45 minuti di fondo lento in Zona 2 (max 130 bpm). Nessun picco, nessuna accelerazione. Solo volume.",
            steps: [
                {"dur": 2700, "pwr": 0.6}
            ],
            maxPwr: 0.6,
            totalDur: 2700
        }
    },
    "Aerobic Capacity 4": {
        theme: "🧱 Il Cedimento Muscolare: Quando Finisce la Benzina",
        intro: "Hai affrontato un'impegnativa piramide di potenza. L'hai scalata con grande autorità, ma la discesa ha presentato un conto salato. Questo è un allenamento che racconta una storia fisiologica chiarissima.",
        highlights: [
            {
                icon: "🏔️",
                title: "1. La Vetta a 252 Watt",
                text: "Hai scalato i blocchi da 140W, 160W, 200W, 230W centrando perfettamente i target, fino a raggiungere il picco della piramide a <strong>252.3W</strong> (159 bpm). Un'esecuzione impeccabile e un dominio totale della macchina."
            },
            {
                icon: "⛽",
                title: "2. Il Serbatoio Vuoto",
                text: "Dopo il picco, sei sceso a 200W senza problemi (200.7W), ma al successivo gradino da 230W c'è stato il <strong>cedimento totale</strong> (76.1W -> 0W). La Frequenza Cardiaca era a 153 bpm, non al massimale: questo significa che non ha ceduto il cuore, ha ceduto il muscolo. Hai esaurito completamente il glicogeno muscolare e le fibre veloci si sono letteralmente spente."
            }
        ],
        analysis: {
            title: "🧬 Analisi: Aerobic Capacity 4 (L'esaurimento del Glicogeno)",
            text: \`Non c'è niente di cui vergognarsi nell'aver fallito l'ultimo intervallo. Negli sport di potenza prolungata, colpire il "muro" muscolare è parte integrante dell'adattamento. <br><br>
                   Il fatto che il tuo cuore fosse a soli 153 bpm nel momento dell'abbandono (rispetto ai 160 bpm toccati poco prima) è la prova del nove: <em>cedimento periferico</em>, non centrale. Le gambe erano vuote. Probabilmente un calo di zuccheri o un mancato recupero dalla sessione precedente.<br><br>
                   <strong>Il Prossimo Step:</strong> Impara ad ascoltare questi segnali. Quando le fibre esplosive sono "fritte", insistere porta solo a infortuni. Fai il carico di carboidrati e dedicati al defaticamento.\`
        },
        nextWorkout: {
            title: "Recovery Row",
            type: "ACTIVE RECOVERY",
            desc: "20 minuti di scioglimento leggero. 20 SPM, niente forza, solo circolazione.",
            steps: [
                {"dur": 1200, "pwr": 0.5}
            ],
            maxPwr: 0.5,
            totalDur: 1200
        }
    },
        theme: "👑 L'Apoteosi del Lattato: Sforzo Massimale",
        intro: "Questa sessione è stata un'escalation chirurgica. Hai affrontato tre blocchi a piramide arrivando ogni volta a sfiorare i tuoi limiti, con una precisione millimetrica sui wattaggi richiesti.",
        highlights: [
            {
                icon: "🎯",
                title: "1. Precisione Svizzera sui 230W",
                text: "Nei tre picchi a 230 Watt hai registrato rispettivamente <strong>231.7W</strong>, <strong>232.2W</strong> e <strong>229.0W</strong>. Aver tenuto una deviazione inferiore all'1% dal target, mentre il corpo urla pietà sotto acido lattico, dimostra una propriocezione e un controllo della potenza eccezionali."
            },
            {
                icon: "❤️",
                title: "2. Il Picco a 179 bpm (La Redline)",
                text: "Nell'ultimo feroce blocco di 2 minuti a 230W (tirato a 28 SPM), il tuo cuore ha toccato i <strong>179 bpm</strong>. Considerando che il tuo massimale teorico è 181, hai letteralmente lavorato al 99% delle tue capacità cardiache. Sei entrato nella <em>Redline</em>, la zona dove il corpo subisce lo stimolo più brutale per l'adattamento del VO2Max."
            }
        ],
        analysis: {
            title: "🧬 Analisi: Aerobic Capacity 6 (La gestione del recupero)",
            text: `Questo allenamento mostra l'importanza di analizzare i dati a blocchi. Guardiamo cosa è successo nei tuoi recuperi (i blocchi da 8 minuti a 160W).<br><br>
                   Nel primo recupero il tuo cuore è sceso a <strong>154 bpm</strong>. Nel secondo recupero è sceso solo a <strong>161 bpm</strong>. Questa si chiama <em>deriva cardiaca</em>: il tuo corpo stava perdendo efficienza nel dissipare il calore e smaltire i metaboliti. <br><br>
                   Quando poi è arrivato l'ultimo blocco (230W a 28 SPM), sei dovuto salire di colpi (da 26 a 28 SPM) per mantenere la stessa potenza, e la tua forza media di picco è leggermente calata (da 57.9 a 57.1 kgf). Il muscolo era vuoto, ma hai compensato con il fiato e la velocità. È un perfetto esempio di come la cadenza salva l'allenamento quando la forza muscolare pura viene a mancare.<br><br>
                   <strong>Il Prossimo Step:</strong> Dopo aver toccato il 99% della tua Frequenza Cardiaca Massima, il tuo sistema nervoso centrale è "fritto". Hai assolutamente bisogno di ricostruire le scorte e riposare. Il prossimo allenamento deve essere un defaticamento totale in Zona 1/2.`
        },
        nextWorkout: {
            title: "Recovery Row",
            type: "ACTIVE RECOVERY",
            desc: "Sessione di recupero attivo per lavare via l'acido lattico e abbassare il cortisolo. Frequenza cardiaca da tenere sotto i 125 bpm.",
            steps: [
                {"dur": 1800, "pwr": 0.5}
            ],
            maxPwr: 0.5,
            totalDur: 1800
        }
    },
    "Regeneration training 4": {
        theme: "Maestria Aerobica: Il Potere del Recupero Attivo",
        intro: "Hai eseguito alla lettera il protocollo di scarico che avevamo pianificato. Dopo il massacro dei 10.4km di ieri, hai abbassato l'ego, hai rallentato la macchina e ti sei concentrato sull'efficienza. Questa sessione è un capolavoro di disciplina neuromuscolare.",
        highlights: [],
        analysis: null,
        nextWorkout: null
    },
    "Aerobic Capacity 2": {
        theme: "🔥 Dominio Anaerobico: Oltre i Limiti",
        intro: "Un HIIT spietato e brutale. Hai affrontato intervalli ad altissima intensità, mettendo alla prova la tua resistenza lattacida e la capacità di recupero. Questa sessione è stata un test incredibile per il tuo sistema neuromuscolare e per la tua tenacia mentale.",
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

    let html = `
    <section class="coach-advice-section" style="margin-top: 2rem; background: var(--bg-surface); backdrop-filter: blur(12px); border: 1px solid var(--border-glass); border-radius: 18px; padding: 2rem; box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-glass); padding-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
            <h2 style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: var(--color-accent); margin: 0;">${analysisData.theme || 'Analisi Coach'}</h2>
            <span style="background: rgba(99, 102, 241, 0.2); color: #6366f1; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; white-space: nowrap;">Analisi Workout (${workout.title})</span>
        </div>
    `;

    if (analysisData.intro) {
        html += `
        <p style="color: var(--text-secondary); font-size: 1.05rem; line-height: 1.6; margin-bottom: 2rem;">
            ${analysisData.intro}
        </p>
        `;
    }

    // Stat Cards
    let peakForce = 0;
    if (workout.smartrower && workout.smartrower.avg_peak_force) {
        peakForce = workout.smartrower.avg_peak_force; // Manca la max vera, uso l'avg peak o max_power surrogato
        // O troviamo il picco dai blocchi:
        const pf = Math.max(...workout.smartrower.blocks.map(b => b.real_peak_force || 0));
        if (pf > 0) peakForce = pf;
    }

    html += `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2.5rem;">
        <div style="background: rgba(255,255,255,0.03); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="color: #9ca3af; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Battito</h4>
            <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                <span style="color: #10b981; font-size: 1.6rem; font-weight: 700;">${workout.avg_hr} bpm</span>
                <span style="color: #ec4899; font-size: 0.95rem;">(Picco: ${workout.max_hr} bpm)</span>
            </div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="color: #9ca3af; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Potenza</h4>
            <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                <span style="color: #3b82f6; font-size: 1.6rem; font-weight: 700;">${workout.avg_power} W</span>
                <span style="color: #9ca3af; font-size: 0.95rem;">(Picco: ${workout.max_power} W)</span>
            </div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="color: #9ca3af; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Cadenza</h4>
            <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                <span style="color: #f59e0b; font-size: 1.6rem; font-weight: 700;">${workout.avg_cadence} SPM</span>
                <span style="color: #9ca3af; font-size: 0.95rem;">(Picco: ${workout.max_cadence} SPM)</span>
            </div>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="color: #9ca3af; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Forza Picco</h4>
            <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                <span style="color: #8b5cf6; font-size: 1.6rem; font-weight: 700;">${peakForce.toFixed(1)} kgf</span>
            </div>
        </div>
    </div>
    `;

    // Highlights
    if (analysisData.highlights && analysisData.highlights.length > 0) {
        html += `<div style="display: flex; flex-direction: column; gap: 2rem;">`;
        analysisData.highlights.forEach(hl => {
            html += `
            <div>
                <h3 style="color: #fff; font-size: 1.3rem; margin-bottom: 0.8rem; display: flex; align-items: center; gap: 0.5rem;">${hl.icon} ${hl.title}</h3>
                <p style="color: var(--text-secondary); line-height: 1.7; font-size: 1.05rem; margin: 0;">${hl.text}</p>
            </div>
            `;
        });
        html += `</div>`;
    }

    // Detailed Analysis
    if (analysisData.analysis) {
        html += `
        <div style="margin-top: 3rem; padding: 2rem; background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.05) 100%); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 16px; position: relative; overflow: hidden;">
            <div style="position: absolute; top: -10px; right: -10px; font-size: 8rem; opacity: 0.05; transform: rotate(15deg); pointer-events: none;">🔥</div>
            <h3 style="color: #ef4444; margin-bottom: 1rem; font-size: 1.4rem; display: flex; align-items: center; gap: 0.5rem; position: relative; z-index: 1;">${analysisData.analysis.title}</h3>
            <p style="color: #fff; font-style: normal; line-height: 1.7; font-size: 1.05rem; margin: 0; position: relative; z-index: 1;">
                ${analysisData.analysis.text}
            </p>
        `;
        
        // Next Workout
        if (analysisData.nextWorkout) {
            const nw = analysisData.nextWorkout;
            let barsHtml = "";
            nw.steps.forEach((s, index) => {
                const width = (s.dur / nw.totalDur) * 100;
                const height = (s.pwr / nw.maxPwr) * 100;
                const color = getPhaseColor(s.pwr);
                const title = `${s.dur}s @ ${Math.round(s.pwr*100)}% FTP`;
                const borderRight = index < nw.steps.length - 1 ? 'border-right: 1px solid rgba(0,0,0,0.3);' : '';
                barsHtml += `<div title="${title}" style="width: ${width}%; height: ${height}%; background-color: ${color}; opacity: 0.9; border-radius: 2px 2px 0 0; ${borderRight}"></div>`;
            });

            html += `
            <div style="margin-top: 2rem; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1.5rem; position: relative; z-index: 1; width: 100%; box-sizing: border-box;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h4 style="color: #fff; font-size: 1.2rem; margin: 0 0 0.5rem 0;">${nw.title}</h4>
                    <span style="background: rgba(59, 130, 246, 0.2); color: #3b82f6; font-size: 0.8rem; font-weight: bold; padding: 4px 10px; border-radius: 12px; letter-spacing: 1px;">${nw.type}</span>
                </div>
                <p style="color: #9ca3af; font-size: 0.95rem; margin: 0 0 1.5rem 0;">${nw.desc}</p>
                <div style="display: flex; align-items: flex-end; height: 120px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 2px; width: 100%; box-sizing: border-box;">
                    ${barsHtml}
                </div>
            </div>
            `;
        }
        
        html += `</div>`; // chiude div margin-top 3rem
    }

    html += `</section>`;
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
