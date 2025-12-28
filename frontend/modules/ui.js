import { SimulationHelpers } from './helpers.js';

export class SimulationUI {
    constructor() {
        this.elements = {};
        this.initializeDOMReferences();
    }

    initializeDOMReferences() {
        // Botones de control
        this.elements.startBtn = document.getElementById('start-btn');
        this.elements.stopBtn = document.getElementById('stop-btn');
        this.elements.pauseBtn = document.getElementById('pause-btn');
        this.elements.resumeBtn = document.getElementById('resume-btn');
        this.elements.resetBtn = document.getElementById('reset-btn');
        this.elements.stepBtn = document.getElementById('step-btn');
        this.elements.updateParamsBtn = document.getElementById('update-params-btn');
        
        // Stats
        this.elements.asexualReproductions = document.getElementById('asexual-reproductions');
        this.elements.canReproduceNow = document.getElementById('can-reproduce-now');
        this.elements.avgOffspring = document.getElementById('avg-offspring');
        this.elements.bacteriaCount = document.getElementById('bacteria-count');
        this.elements.phagocyteCount = document.getElementById('phagocyte-count');
        this.elements.generation = document.getElementById('generation');
        this.elements.totalCaptures = document.getElementById('total-captures');
        this.elements.totalReproductions = document.getElementById('total-reproductions');
        this.elements.runTime = document.getElementById('run-time');
        this.elements.avgGenTime = document.getElementById('avg-gen-time');
        this.elements.simulationFps = document.getElementById('simulation-fps');
        
        this.elements.notification = document.getElementById('notification');
        this.elements.statusIndicator = document.getElementById('status-indicator');
    }

    updateControls(isRunning) {
        this.elements.startBtn.disabled = isRunning;
        this.elements.stopBtn.disabled = !isRunning;
        this.elements.pauseBtn.disabled = !isRunning;
        this.elements.resumeBtn.disabled = isRunning;
        this.elements.resetBtn.disabled = isRunning;
        
        this.elements.statusIndicator.textContent = isRunning ? 'En ejecución' : 'Detenido';
        this.elements.statusIndicator.className = isRunning ? 'status-running' : 'status-stopped';
    }

    updateGeneration(gen) {
        this.elements.generation.textContent = gen;
    }

    updateStats(state) {
        if (!state) return;
        
        this.updateGeneration(state.generation);
        this.elements.bacteriaCount.textContent = state.stats.populations.bacteria;
        this.elements.phagocyteCount.textContent = state.stats.populations.phagocytes;
        this.elements.totalCaptures.textContent = state.stats.captures;
        this.elements.totalReproductions.textContent = state.stats.reproductions;
        
        if (state.stats && state.stats.reproduction) {
            this.elements.asexualReproductions.textContent = state.stats.reproduction.total_asexual || 0;
            this.elements.canReproduceNow.textContent = state.stats.reproduction.can_reproduce_now || 0;
            this.elements.avgOffspring.textContent = state.stats.reproduction.average_offspring?.toFixed(1) || '0.0';
        }
    }

    updatePerformance(stats) {
        if (!stats) return;
        const runTime = Math.round(stats.summary.run_time);
        this.elements.runTime.textContent = `${runTime}s`;
        
        if (stats.performance) {
            this.elements.avgGenTime.textContent = stats.performance.avg_generation_time.toFixed(4) + 's';
            this.elements.simulationFps.textContent = stats.performance.fps.toFixed(1);
        }
    }

    showNotification(message, type = 'info') {
        const el = this.elements.notification;
        el.textContent = message;
        el.className = `notification notification-${type}`;
        el.style.display = 'block';
        setTimeout(() => { el.style.display = 'none'; }, 3000);
    }

    getParametersFromForm() {
        const params = {};
        document.querySelectorAll('.parameter-input').forEach(input => {
            const key = input.id.replace('param-', '');
            let value = input.value;
            if (input.type === 'number') value = parseFloat(value);
            else if (input.type === 'color') value = SimulationHelpers.hexToRgb(value);
            params[key] = value;
        });
        return params;
    }

    populateParameterForm(params) {
        for (const [key, value] of Object.entries(params)) {
            const input = document.getElementById(`param-${key}`);
            if (input) {
                if (Array.isArray(value)) {
                    if (input.type === 'color') input.value = SimulationHelpers.rgbToHex(value);
                    else input.value = value.join(',');
                } else {
                    input.value = value;
                }
            }
        }
    }
}