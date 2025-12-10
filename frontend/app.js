/**
 * Clase principal para la simulación de coevolución
 * Usa AJAX y polling en lugar de WebSockets
 */
class CoevolutionSimulation {
    constructor() {
        this.baseUrl = window.location.origin;
        this.isRunning = false;
        this.currentGeneration = 0;
        this.lastPolledGeneration = 0;
        
        // Intervalos de polling
        this.statePollingInterval = null;
        this.statsPollingInterval = null;
        this.statusPollingInterval = null;
        
        // Caché local para optimizar
        this.cachedState = null;
        this.cachedStats = null;
        this.lastUpdateTime = 0;
        
        // Referencias a elementos DOM
        this.initializeDOMReferences();
        
        // Inicializar gráficos
        this.initializeCharts();
        
        // Configurar event listeners
        this.initializeEventListeners();
        
        // Cargar estado inicial
        this.loadInitialState();
        
        // Iniciar polling de estado
        this.startStatusPolling();
    }
    
    initializeDOMReferences() {
        // Canvas y contexto
        this.canvas = document.getElementById('simulation-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Botones de control
        this.startBtn = document.getElementById('start-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.pauseBtn = document.getElementById('pause-btn');
        this.resumeBtn = document.getElementById('resume-btn');
        this.resetBtn = document.getElementById('reset-btn');
        this.stepBtn = document.getElementById('step-btn');
        this.updateParamsBtn = document.getElementById('update-params-btn');
        
        // Elementos de estadísticas
        this.bacteriaCountEl = document.getElementById('bacteria-count');
        this.phagocyteCountEl = document.getElementById('phagocyte-count');
        this.generationEl = document.getElementById('generation');
        this.totalCapturesEl = document.getElementById('total-captures');
        this.totalReproductionsEl = document.getElementById('total-reproductions');
        this.runTimeEl = document.getElementById('run-time');
        this.avgGenTimeEl = document.getElementById('avg-gen-time');
        this.simulationFpsEl = document.getElementById('simulation-fps');
        
        // Notificación
        this.notificationEl = document.getElementById('notification');
    }
    
    initializeCharts() {
        // Gráfico de fitness
        this.fitnessChart = new Chart(
            document.getElementById('fitness-chart').getContext('2d'),
            {
                type: 'line',
                data: {
                    datasets: [
                        {
                            label: 'Bacterias (Avg)',
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            data: []
                        },
                        {
                            label: 'Fagocitos (Avg)',
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            data: []
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'linear',
                            position: 'bottom',
                            title: {
                                display: true,
                                text: 'Generación'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            max: 1.0,
                            title: {
                                display: true,
                                text: 'Fitness'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    }
                }
            }
        );
        
        // Gráfico de población
        this.populationChart = new Chart(
            document.getElementById('population-chart').getContext('2d'),
            {
                type: 'line',
                data: {
                    datasets: [
                        {
                            label: 'Bacterias',
                            borderColor: 'rgb(54, 162, 235)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            data: []
                        },
                        {
                            label: 'Fagocitos',
                            borderColor: 'rgb(255, 159, 64)',
                            backgroundColor: 'rgba(255, 159, 64, 0.2)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            data: []
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            type: 'linear',
                            position: 'bottom',
                            title: {
                                display: true,
                                text: 'Generación'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Población'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    }
                }
            }
        );
    }
    
    initializeEventListeners() {
        // Botones de control
        this.startBtn.addEventListener('click', () => this.startSimulation());
        this.stopBtn.addEventListener('click', () => this.stopSimulation());
        this.pauseBtn.addEventListener('click', () => this.pauseSimulation());
        this.resumeBtn.addEventListener('click', () => this.resumeSimulation());
        this.resetBtn.addEventListener('click', () => this.resetSimulation());
        this.stepBtn.addEventListener('click', () => this.stepSimulation());
        this.updateParamsBtn.addEventListener('click', () => this.updateParameters());
        
        // Ajustar tamaño del canvas cuando cambia la ventana
        window.addEventListener('resize', () => this.adjustCanvasSize());
    }
    
    adjustCanvasSize() {
        // Mantener proporciones pero ajustar al contenedor
        const container = this.canvas.parentElement;
        const containerWidth = container.clientWidth;
        
        // Mantener relación de aspecto 4:3
        const targetHeight = (containerWidth * 3) / 4;
        
        if (this.canvas.width !== containerWidth || this.canvas.height !== targetHeight) {
            this.canvas.width = containerWidth;
            this.canvas.height = targetHeight;
            
            // Si hay estado en caché, volver a renderizar
            if (this.cachedState) {
                this.renderCanvas(this.cachedState);
            }
        }
    }
    
    // ==================== API METHODS ====================
    
    async fetchAPI(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}/api${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error en ${endpoint}:`, error);
            this.showNotification(`Error: ${error.message}`, 'error');
            throw error;
        }
    }
    
    // ==================== SIMULATION CONTROL ====================
    
    async startSimulation() {
        try {
            const params = this.getParametersFromForm();
            
            const result = await this.fetchAPI('/simulation/start', {
                method: 'POST',
                body: JSON.stringify(params)
            });
            
            this.showNotification('Simulación iniciada', 'success');
            this.isRunning = true;
            this.updateUI();
            this.startPolling();
            
        } catch (error) {
            // Error ya manejado en fetchAPI
        }
    }
    
    async stopSimulation() {
        try {
            await this.fetchAPI('/simulation/stop', { method: 'POST' });
            this.showNotification('Simulación detenida', 'success');
            this.isRunning = false;
            this.updateUI();
            this.stopPolling();
            
        } catch (error) {
            // Error ya manejado en fetchAPI
        }
    }
    
    async pauseSimulation() {
        try {
            await this.fetchAPI('/simulation/pause', { method: 'POST' });
            this.showNotification('Simulación pausada', 'success');
            this.isRunning = false;
            this.updateUI();
            this.stopStatePolling();
            
        } catch (error) {
            // Error ya manejado en fetchAPI
        }
    }
    
    async resumeSimulation() {
        try {
            await this.fetchAPI('/simulation/resume', { method: 'POST' });
            this.showNotification('Simulación reanudada', 'success');
            this.isRunning = true;
            this.updateUI();
            this.startPolling();
            
        } catch (error) {
            // Error ya manejado en fetchAPI
        }
    }
    
    async resetSimulation() {
        try {
            await this.fetchAPI('/simulation/reset', { method: 'POST' });
            this.showNotification('Simulación reiniciada', 'success');
            this.clearCharts();
            this.updateUI();
            
        } catch (error) {
            // Error ya manejado en fetchAPI
        }
    }
    
    async stepSimulation() {
        try {
            const result = await this.fetchAPI('/simulation/step', { method: 'POST' });
            this.showNotification('Paso ejecutado', 'success');
            this.currentGeneration = result.generation;
            await this.fetchAndUpdateState();
            
        } catch (error) {
            // Error ya manejado en fetchAPI
        }
    }
    
    async updateParameters() {
        try {
            const params = this.getParametersFromForm();
            
            await this.fetchAPI('/parameters', {
                method: 'POST',
                body: JSON.stringify(params)
            });
            
            this.showNotification('Parámetros actualizados', 'success');
            
        } catch (error) {
            // Error ya manejado en fetchAPI
        }
    }
    
    // ==================== POLLING METHODS ====================
    
    startStatusPolling() {
        // Polling para estado general (cada 5 segundos)
        this.statusPollingInterval = setInterval(async () => {
            await this.checkSimulationStatus();
        }, 5000);
    }
    
    startPolling() {
        // Detener polling anteriores
        this.stopPolling();
        
        // Polling para estado de simulación (rápido, cada 100ms)
        this.statePollingInterval = setInterval(async () => {
            await this.fetchAndUpdateState();
        }, 100);
        
        // Polling para estadísticas (lento, cada 1 segundo)
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
            // Cargar parámetros por defecto
            const params = await this.fetchAPI('/parameters');
            this.populateParameterForm(params);
            
            // Verificar estado actual
            await this.checkSimulationStatus();
            
            // Ajustar tamaño inicial del canvas
            setTimeout(() => this.adjustCanvasSize(), 100);
            
        } catch (error) {
            console.error('Error cargando estado inicial:', error);
        }
    }
    
    async checkSimulationStatus() {
        try {
            const status = await this.fetchAPI('/simulation/status');
            
            this.isRunning = status.is_running;
            this.currentGeneration = status.current_generation || status.generation || 0;
            
            this.updateUI();
            
            // Si la simulación está corriendo pero no tenemos polling activo
            if (this.isRunning && !this.statePollingInterval) {
                this.startPolling();
            }
            // Si la simulación no está corriendo pero tenemos polling activo
            else if (!this.isRunning && this.statePollingInterval) {
                this.stopPolling();
            }
            
        } catch (error) {
            console.error('Error verificando estado:', error);
        }
    }
    
    async fetchAndUpdateState() {
        try {
            // Usar endpoint optimizado que solo devuelve cambios
            const updates = await this.fetchAPI(
                `/simulation/updates?since=${this.lastPolledGeneration}&state=true&stats=false`
            );
            
            if (updates.has_updates) {
                this.lastPolledGeneration = updates.current_generation;
                this.currentGeneration = updates.current_generation;
                
                if (updates.state) {
                    this.updateSimulationState(updates.state);
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
            const stats = await this.fetchAPI('/simulation/stats');
            this.updateStatistics(stats);
            this.cachedStats = stats;
            
        } catch (error) {
            console.error('Error obteniendo estadísticas:', error);
        }
    }
    
    // ==================== UI UPDATES ====================
    
    updateSimulationState(state) {
        if (!state) return;
        
        // Actualizar contadores
        this.generationEl.textContent = state.generation;
        this.bacteriaCountEl.textContent = state.stats.populations.bacteria;
        this.phagocyteCountEl.textContent = state.stats.populations.phagocytes;
        this.totalCapturesEl.textContent = state.stats.captures;
        this.totalReproductionsEl.textContent = state.stats.reproductions;
        
        // Actualizar gráficos
        this.updateCharts(state);
        
        // Renderizar canvas
        this.renderCanvas(state);
    }
    
    updateStatistics(stats) {
        if (!stats) return;
        
        // Actualizar tiempo de ejecución
        const runTime = Math.round(stats.summary.run_time);
        this.runTimeEl.textContent = `${runTime}s`;
        
        // Actualizar rendimiento
        if (stats.performance) {
            this.avgGenTimeEl.textContent = stats.performance.avg_generation_time.toFixed(4) + 's';
            this.simulationFpsEl.textContent = stats.performance.fps.toFixed(1);
        }
    }
    
    updateCharts(state) {
        const generation = state.generation;
        const fitness = state.stats.fitness;
        
        // Actualizar gráfico de fitness
        this.fitnessChart.data.datasets[0].data.push({
            x: generation,
            y: fitness.bacteria.avg
        });
        
        this.fitnessChart.data.datasets[1].data.push({
            x: generation,
            y: fitness.phagocytes.avg
        });
        
        // Mantener solo últimos 100 puntos
        const maxPoints = 100;
        if (this.fitnessChart.data.datasets[0].data.length > maxPoints) {
            this.fitnessChart.data.datasets[0].data.shift();
            this.fitnessChart.data.datasets[1].data.shift();
        }
        
        this.fitnessChart.update('none');
        
        // Actualizar gráfico de población
        this.populationChart.data.datasets[0].data.push({
            x: generation,
            y: state.stats.populations.bacteria
        });
        
        this.populationChart.data.datasets[1].data.push({
            x: generation,
            y: state.stats.populations.phagocytes
        });
        
        if (this.populationChart.data.datasets[0].data.length > maxPoints) {
            this.populationChart.data.datasets[0].data.shift();
            this.populationChart.data.datasets[1].data.shift();
        }
        
        this.populationChart.update('none');
    }
    
    renderCanvas(state) {
        if (!state || !state.environment || !state.agents) return;
        
        const { width, height, background_color } = state.environment;
        const agents = state.agents;
        
        // Ajustar tamaño del canvas si es necesario
        if (this.canvas.width !== width) {
            this.canvas.width = width;
        }
        if (this.canvas.height !== height) {
            this.canvas.height = height;
        }
        
        // Limpiar canvas
        this.ctx.fillStyle = `rgb(${background_color.join(',')})`;
        this.ctx.fillRect(0, 0, width, height);
        
        // Dibujar bacterias primero (para que queden detrás)
        agents.bacteria.forEach(bacteria => {
            this.drawAgent(bacteria, false);
        });
        
        // Dibujar fagocitos después (para que queden encima)
        agents.phagocytes.forEach(phagocyte => {
            this.drawAgent(phagocyte, true);
        });
    }
    
    drawAgent(agent, isPhagocyte = false) {
        const x = agent.x;
        const y = agent.y;
        const color = agent.color;
        
        this.ctx.save();
        
        if (isPhagocyte) {
            // Dibujar fagocito como círculo con centro negro
            const radius = 8; // Tamaño fijo para fagocitos
            
            // Contorno de color (rasgo evolutivo)
            this.ctx.strokeStyle = `rgb(${color.join(',')})`;
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.arc(x, y, radius, 0, Math.PI * 2);
            this.ctx.stroke();
            
            // Centro negro
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
            this.ctx.beginPath();
            this.ctx.arc(x, y, radius * 0.6, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Punto blanco en el centro para mejor visibilidad
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            this.ctx.beginPath();
            this.ctx.arc(x, y, radius * 0.2, 0, Math.PI * 2);
            this.ctx.fill();
            
        } else {
            // Dibujar bacteria como bastón (bacilo)
            // Usar genes si están disponibles, sino valores por defecto
            const lengthGene = agent.length_gene || agent.genome?.length_gene || 0.5;
            const widthGene = agent.width_gene || agent.genome?.width_gene || 0.5;
            
            // Calcular dimensiones del bastón
            const baseLength = 12;
            const length = baseLength * (0.8 + 0.4 * lengthGene);
            
            const baseWidth = 4.5;
            const width = baseWidth * (0.7 + 0.6 * widthGene);
            
            // Calcular dirección del movimiento
            let direction = 0;
            if (agent.direction !== undefined) {
                direction = agent.direction;
            } else if (agent.vx !== undefined && agent.vy !== undefined) {
                direction = Math.atan2(agent.vy, agent.vx);
            }
            
            // Puntos para el bastón (cápsula alargada)
            const cosDir = Math.cos(direction);
            const sinDir = Math.sin(direction);
            
            // Dibujar el bastón (cápsula alargada)
            this.ctx.strokeStyle = 'rgba(0, 0, 0, 0.8)';  // Contorno negro
            this.ctx.lineWidth = 1;
            this.ctx.fillStyle = `rgb(${color.join(',')})`;  // Centro con color evolutivo
            
            // Cuerpo rectangular del bastón
            this.ctx.save();
            this.ctx.translate(x, y);
            this.ctx.rotate(direction);
            
            // Cuerpo rectangular
            const halfLength = length / 2;
            const halfWidth = width / 2;
            
            // Rectángulo principal
            this.ctx.fillRect(-halfLength, -halfWidth, length, width);
            this.ctx.strokeRect(-halfLength, -halfWidth, length, width);
            
            // Extremos redondeados
            this.ctx.beginPath();
            this.ctx.arc(-halfLength, 0, halfWidth, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.stroke();
            
            this.ctx.beginPath();
            this.ctx.arc(halfLength, 0, halfWidth, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.stroke();
            
            this.ctx.restore();
        }
        
        this.ctx.restore();
    }
    
    updateUI() {
        // Actualizar estado de botones
        this.startBtn.disabled = this.isRunning;
        this.stopBtn.disabled = !this.isRunning;
        this.pauseBtn.disabled = !this.isRunning;
        this.resumeBtn.disabled = this.isRunning;
        this.resetBtn.disabled = this.isRunning;
        
        // Actualizar indicador de estado
        const statusIndicator = document.getElementById('status-indicator');
        statusIndicator.textContent = this.isRunning ? 'En ejecución' : 'Detenido';
        statusIndicator.className = this.isRunning ? 'status-running' : 'status-stopped';
        
        // Actualizar generación actual
        this.generationEl.textContent = this.currentGeneration;
    }
    
    clearCharts() {
        // Limpiar datos de gráficos
        this.fitnessChart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });
        this.fitnessChart.update();
        
        this.populationChart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });
        this.populationChart.update();
    }
    
    // ==================== PARAMETER MANAGEMENT ====================
    
    getParametersFromForm() {
        const params = {};
        
        // Obtener todos los inputs de parámetros
        document.querySelectorAll('.parameter-input').forEach(input => {
            const key = input.id.replace('param-', '');
            let value = input.value;
            
            // Convertir tipos según el input
            if (input.type === 'number') {
                value = parseFloat(value);
            } else if (input.type === 'color') {
                value = this.hexToRgb(value);
            }
            
            params[key] = value;
        });
        
        return params;
    }
    
    populateParameterForm(params) {
        for (const [key, value] of Object.entries(params)) {
            const input = document.getElementById(`param-${key}`);
            if (input) {
                if (Array.isArray(value)) {
                    // Convertir array a string para inputs de color
                    if (input.type === 'color') {
                        input.value = this.rgbToHex(value);
                    } else {
                        input.value = value.join(',');
                    }
                } else {
                    input.value = value;
                }
            }
        }
    }
    
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? [
            parseInt(result[1], 16),
            parseInt(result[2], 16),
            parseInt(result[3], 16)
        ] : [240, 240, 240];
    }
    
    rgbToHex(rgb) {
        return '#' + rgb.map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }
    
    // ==================== UTILITIES ====================
    
    showNotification(message, type = 'info') {
        this.notificationEl.textContent = message;
        this.notificationEl.className = `notification notification-${type}`;
        this.notificationEl.style.display = 'block';
        
        // Ocultar después de 3 segundos
        setTimeout(() => {
            this.notificationEl.style.display = 'none';
        }, 3000);
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.simulation = new CoevolutionSimulation();
});