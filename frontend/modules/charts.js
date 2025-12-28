export class SimulationCharts {
    constructor() {
        this.fitnessChart = null;
        this.populationChart = null;
        this.initialize();
    }

    initialize() {
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
                        x: { type: 'linear', position: 'bottom', title: { display: true, text: 'Generación' } },
                        y: { beginAtZero: true, max: 1.0, title: { display: true, text: 'Fitness' } }
                    },
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: { mode: 'index', intersect: false }
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
                        x: { type: 'linear', position: 'bottom', title: { display: true, text: 'Generación' } },
                        y: { beginAtZero: true, title: { display: true, text: 'Población' } }
                    },
                    plugins: { legend: { position: 'top' } }
                }
            }
        );
    }

    update(state) {
        const generation = state.generation;
        const fitness = state.stats.fitness;
        const maxPoints = 100;

        // Update Fitness
        this.fitnessChart.data.datasets[0].data.push({ x: generation, y: fitness.bacteria.avg });
        this.fitnessChart.data.datasets[1].data.push({ x: generation, y: fitness.phagocytes.avg });

        if (this.fitnessChart.data.datasets[0].data.length > maxPoints) {
            this.fitnessChart.data.datasets[0].data.shift();
            this.fitnessChart.data.datasets[1].data.shift();
        }
        this.fitnessChart.update('none');

        // Update Population
        this.populationChart.data.datasets[0].data.push({ x: generation, y: state.stats.populations.bacteria });
        this.populationChart.data.datasets[1].data.push({ x: generation, y: state.stats.populations.phagocytes });

        if (this.populationChart.data.datasets[0].data.length > maxPoints) {
            this.populationChart.data.datasets[0].data.shift();
            this.populationChart.data.datasets[1].data.shift();
        }
        this.populationChart.update('none');
    }

    clear() {
        this.fitnessChart.data.datasets.forEach(d => d.data = []);
        this.fitnessChart.update();
        this.populationChart.data.datasets.forEach(d => d.data = []);
        this.populationChart.update();
    }
}