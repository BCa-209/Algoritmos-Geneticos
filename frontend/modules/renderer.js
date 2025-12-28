export class SimulationRenderer {
    constructor() {
        this.canvas = document.getElementById('simulation-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.glucoseImage = null;
        this.loadGlucoseImage();
        
        // Listener para resize
        window.addEventListener('resize', () => this.adjustCanvasSize());
        // Ajuste inicial
        setTimeout(() => this.adjustCanvasSize(), 100);
    }

    loadGlucoseImage() {
        this.glucoseImage = new Image();
        this.glucoseImage.src = 'assets/glc.webp';
        
        this.glucoseImage.onload = () => {
            console.log('Imagen de glucosa cargada correctamente');
        };
        
        this.glucoseImage.onerror = () => {
            console.error('Error cargando la imagen de glucosa. Usando dibujo vectorial.');
            this.glucoseImage = null;
        };
    }

    adjustCanvasSize(cachedState = null) {
        const container = this.canvas.parentElement;
        const containerWidth = container.clientWidth;
        const targetHeight = (containerWidth * 3) / 4;
        
        if (this.canvas.width !== containerWidth || this.canvas.height !== targetHeight) {
            this.canvas.width = containerWidth;
            this.canvas.height = targetHeight;
            if (cachedState) this.render(cachedState);
        }
    }

    render(state) {
        if (!state || !state.environment || !state.agents) return;
        
        const { width, height, background_color } = state.environment;
        const agents = state.agents;
        
        // Sincronizar dimensiones lógicas si es necesario
        if (this.canvas.width !== width) this.canvas.width = width;
        if (this.canvas.height !== height) this.canvas.height = height;
        
        // Fondo
        this.ctx.fillStyle = `rgb(${background_color.join(',')})`;
        this.ctx.fillRect(0, 0, width, height);
        
        // Glucosa
        if (agents.glucose) {
            agents.glucose.forEach(g => {
                if (this.glucoseImage && this.glucoseImage.complete) {
                    this.drawGlucoseWithImage(g);
                } else {
                    this.drawGlucose(g);
                }
            });
        }
        
        // Agentes
        agents.bacteria.forEach(b => this.drawAgent(b, false));
        agents.phagocytes.forEach(p => this.drawAgent(p, true));
    }

    drawGlucose(glucose) {
        if (!glucose || glucose.consumed || glucose.size <= 0) return;
        
        const ctx = this.ctx;
        ctx.save();
        ctx.translate(glucose.x, glucose.y);
        
        const gradient = ctx.createRadialGradient(0, 0, glucose.size * 0.3, 0, 0, glucose.size);
        const energyRatio = glucose.energy / (glucose.size * 5);
        const hue = 50 + energyRatio * 10;
        const saturation = 80 + energyRatio * 20;
        const lightness = 50 + energyRatio * 20;
        
        gradient.addColorStop(0, `hsla(${hue}, ${saturation}%, ${lightness}%, 0.9)`);
        gradient.addColorStop(0.7, `hsla(${hue}, ${saturation}%, ${lightness - 10}%, 0.6)`);
        gradient.addColorStop(1, `hsla(${hue}, ${saturation}%, ${lightness - 20}%, 0.3)`);
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(0, 0, glucose.size, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.fillStyle = `hsla(${hue}, ${saturation}%, ${lightness + 10}%, 0.4)`;
        ctx.beginPath();
        ctx.arc(0, 0, glucose.size * 0.4, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }

    drawGlucoseWithImage(glucose) {
        if (!glucose || glucose.consumed || glucose.size <= 0) return;
        
        if (this.glucoseImage && this.glucoseImage.complete && this.glucoseImage.width > 0) {
            const imageSize = glucose.size * 2.5;
            this.ctx.save();
            this.ctx.translate(glucose.x, glucose.y);
            const opacity = Math.min(1.0, 0.3 + (glucose.energy / 100) * 0.7);
            this.ctx.globalAlpha = opacity;
            
            this.ctx.drawImage(this.glucoseImage, -imageSize / 2, -imageSize / 2, imageSize, imageSize);
            
            this.ctx.globalAlpha = opacity * 0.3;
            this.ctx.beginPath();
            this.ctx.arc(0, 0, imageSize * 0.6, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(255, 255, 200, 0.5)`;
            this.ctx.fill();
            this.ctx.restore();
        } else {
            this.drawGlucose(glucose);
        }
    }

    drawAgent(agent, isPhagocyte = false) {
        const x = agent.x;
        const y = agent.y;
        const color = agent.color;
        
        this.ctx.save();
        
        if (isPhagocyte) {
            const radius = 8;
            this.ctx.strokeStyle = `rgb(${color.join(',')})`;
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.arc(x, y, radius, 0, Math.PI * 2);
            this.ctx.stroke();
            
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
            this.ctx.beginPath();
            this.ctx.arc(x, y, radius * 0.6, 0, Math.PI * 2);
            this.ctx.fill();
            
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            this.ctx.beginPath();
            this.ctx.arc(x, y, radius * 0.2, 0, Math.PI * 2);
            this.ctx.fill();
        } else {
            const lengthGene = agent.length_gene || agent.genome?.length_gene || 0.5;
            const widthGene = agent.width_gene || agent.genome?.width_gene || 0.5;
            
            const baseLength = 12;
            const length = baseLength * (0.8 + 0.4 * lengthGene);
            const baseWidth = 4.5;
            const width = baseWidth * (0.7 + 0.6 * widthGene);
            
            let direction = 0;
            if (agent.direction !== undefined) direction = agent.direction;
            else if (agent.vx !== undefined && agent.vy !== undefined) direction = Math.atan2(agent.vy, agent.vx);
            
            if (agent.can_reproduce) this.drawReproductionIndicator(x, y);
            
            this.ctx.strokeStyle = 'rgba(0, 0, 0, 0.8)';
            this.ctx.lineWidth = 1;
            this.ctx.fillStyle = `rgb(${color.join(',')})`;
            
            this.ctx.save();
            this.ctx.translate(x, y);
            this.ctx.rotate(direction);
            
            const halfLength = length / 2;
            const halfWidth = width / 2;
            
            this.ctx.fillRect(-halfLength, -halfWidth, length, width);
            this.ctx.strokeRect(-halfLength, -halfWidth, length, width);
            
            this.ctx.beginPath();
            this.ctx.arc(-halfLength, 0, halfWidth, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.stroke();
            
            this.ctx.beginPath();
            this.ctx.arc(halfLength, 0, halfWidth, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.stroke();
            this.ctx.restore();

            if (agent.offspring_count > 0) this.drawOffspringCount(x, y, agent.offspring_count);
        }
        this.ctx.restore();
    }

    drawReproductionIndicator(x, y) {
        this.ctx.save();
        this.ctx.translate(x, y);
        const pulse = (Date.now() % 2000) / 2000;
        const alpha = 0.3 + 0.3 * Math.sin(pulse * Math.PI * 2);
        const radius = 15 + 5 * Math.sin(pulse * Math.PI * 2);
        
        this.ctx.strokeStyle = `rgba(0, 255, 0, ${alpha})`;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(0, 0, radius, 0, Math.PI * 2);
        this.ctx.stroke();
        
        this.ctx.fillStyle = `rgba(255, 215, 0, ${alpha})`;
        this.ctx.beginPath();
        this.ctx.arc(0, 0, 3, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();
    }

    drawOffspringCount(x, y, count) {
        this.ctx.save();
        this.ctx.translate(x, y - 20);
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        this.ctx.beginPath();
        this.ctx.arc(0, 0, 12, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.fillStyle = 'white';
        this.ctx.font = 'bold 10px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(count, 0, 0);
        this.ctx.restore();
    }
}