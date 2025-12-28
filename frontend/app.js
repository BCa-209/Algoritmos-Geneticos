import { SimulationAPI } from './modules/api.js';
import { SimulationRenderer } from './modules/renderer.js';
import { SimulationCharts } from './modules/charts.js';
import { SimulationUI } from './modules/ui.js';

/**
 * Clase principal para la simulación de coevolución
 * Orquesta los módulos de UI, API, Renderizado y Gráficos
 */
class CoevolutionSimulation {
    constructor() {
        this.isRunning = false;
        this.currentGeneration = 0;
        this.lastPolledGeneration = 0;
        
        // Intervalos
        this.statePollingInterval = null;
        this.statsPollingInterval = null;
        this.statusPollingInterval = null;
        
        // Caché
        this.cachedState = null;
        this.cachedStats = null;
        this.lastUpdateTime = 0;

        // Inicializar módulos
        this.api = new SimulationAPI(window.location.origin);
        this.ui = new SimulationUI();
        this.renderer = new SimulationRenderer();
        this.charts = new SimulationCharts();

        // Configurar Listeners
        this.initializeEventListeners();
        
        // Cargar estado inicial
        this.loadInitialState();
        
        // Iniciar polling
        this.startStatusPolling();
    }

    initializeEventListeners() {
        const els = this.ui.elements;
        
        els.startBtn.addEventListener('click', () => this.startSimulation());
        els.stopBtn.addEventListener('click', () => this.stopSimulation());
        els.pauseBtn.addEventListener('click', () => this.pauseSimulation());
        els.resumeBtn.addEventListener('click', () => this.resumeSimulation());
        els.resetBtn.addEventListener('click', () => this.resetSimulation());
        els.stepBtn.addEventListener('click', () => this.stepSimulation());
        els.updateParamsBtn.addEventListener('click', () => this.updateParameters());
    }

    // ==================== SIMULATION CONTROL ====================
    
    async startSimulation() {
        try {
            const params = this.ui.getParametersFromForm();
            await this.api.fetch('/simulation/start', { method: 'POST', body: JSON.stringify(params) });
            
            this.ui.showNotification('Simulación iniciada', 'success');
            this.isRunning = true;
            this.ui.updateControls(true);
            this.startPolling();
        } catch (error) {
            this.ui.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    async stopSimulation() {
        try {
            await this.api.fetch('/simulation/stop', { method: 'POST' });
            this.ui.showNotification('Simulación detenida', 'success');
            this.isRunning = false;
            this.ui.updateControls(false);
            this.stopPolling();
        } catch (error) {
            this.ui.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    async pauseSimulation() {
        try {
            await this.api.fetch('/simulation/pause', { method: 'POST' });
            this.ui.showNotification('Simulación pausada', 'success');
            this.isRunning = false;
            this.ui.updateControls(false);
            this.stopStatePolling();
        } catch (error) {
            this.ui.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    async resumeSimulation() {
        try {
            await this.api.fetch('/simulation/resume', { method: 'POST' });
            this.ui.showNotification('Simulación reanudada', 'success');
            this.isRunning = true;
            this.ui.updateControls(true);
            this.startPolling();
        } catch (error) {
            this.ui.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    async resetSimulation() {
        try {
            await this.api.fetch('/simulation/reset', { method: 'POST' });
            this.ui.showNotification('Simulación reiniciada', 'success');
            this.charts.clear();
            this.ui.updateControls(this.isRunning);
        } catch (error) {
            this.ui.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    async stepSimulation() {
        try {
            const result = await this.api.fetch('/simulation/step', { method: 'POST' });
            this.ui.showNotification('Paso ejecutado', 'success');
            this.currentGeneration = result.generation;
            await this.fetchAndUpdateState();
        } catch (error) {
            this.ui.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    async updateParameters() {
        try {
            const params = this.ui.getParametersFromForm();
            await this.api.fetch('/parameters', { method: 'POST', body: JSON.stringify(params) });
            this.ui.showNotification('Parámetros actualizados', 'success');
        } catch (error) {
            this.ui.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    // ==================== POLLING METHODS ====================
    
    startStatusPolling() {
        this.statusPollingInterval = setInterval(async () => {
            await this.checkSimulationStatus();
        }, 5000);
    }
    
    startPolling() {
        this.stopPolling();
        // Polling para estado (rápido)
        this.statePollingInterval = setInterval(async () => {
            await this.fetchAndUpdateState();
        }, 100);
        // Polling para estadísticas (lento)
        this.statsPollingInterval = setInterval(async () => {
            await this.fetchAndUpdateStats();
        }, 1000);
    }
    
    stopPolling() {
        this.stopStatePolling();
        this.stopStatsPolling();
    }
    
    stopStatePolling() {
        if (this.statePollingInterval) {
            clearInterval(this.statePollingInterval);
            this.statePollingInterval = null;
        }
    }
    
    stopStatsPolling() {
        if (this.statsPollingInterval) {
            clearInterval(this.statsPollingInterval);
            this.statsPollingInterval = null;
        }
    }
    
    // ==================== DATA FETCHING ====================
    
    async loadInitialState() {
        try {
            const params = await this.api.fetch('/parameters');
            this.ui.populateParameterForm(params);
            
            await this.checkSimulationStatus();
            // Render inicial si es necesario
            setTimeout(() => this.renderer.adjustCanvasSize(), 100);
        } catch (error) {
            console.error('Error cargando estado inicial:', error);
        }
    }
    
    async checkSimulationStatus() {
        try {
            const status = await this.api.fetch('/simulation/status');
            
            this.isRunning = status.is_running;
            this.currentGeneration = status.current_generation || status.generation || 0;
            
            this.ui.updateControls(this.isRunning);
            this.ui.updateGeneration(this.currentGeneration);
            
            if (this.isRunning && !this.statePollingInterval) {
                this.startPolling();
            } else if (!this.isRunning && this.statePollingInterval) {
                this.stopPolling();
            }
        } catch (error) {
            console.error('Error verificando estado:', error);
        }
    }
    
    async fetchAndUpdateState() {
        try {
            const updates = await this.api.fetch(
                `/simulation/updates?since=${this.lastPolledGeneration}&state=true&stats=false`
            );
            
            if (updates.has_updates) {
                this.lastPolledGeneration = updates.current_generation;
                this.currentGeneration = updates.current_generation;
                
                if (updates.state) {
                    this.updateState(updates.state);
                    this.cachedState = updates.state;
                    this.lastUpdateTime = Date.now();
                }
            }
        } catch (error) {
            console.error('Error obteniendo estado:', error);
        }
    }
    
    async fetchAndUpdateStats() {
        try {
            const stats = await this.api.fetch('/simulation/stats');
            this.ui.updatePerformance(stats);
            this.cachedStats = stats;
        } catch (error) {
            console.error('Error obteniendo estadísticas:', error);
        }
    }

    updateState(state) {
        if (!state) return;
        
        // Actualizar UI
        this.ui.updateStats(state);
        
        // Actualizar Gráficos
        this.charts.update(state);
        
        // Renderizar Canvas
        this.renderer.render(state);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.simulation = new CoevolutionSimulation();
});