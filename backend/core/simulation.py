"""
Clase principal de simulación
"""
import numpy as np
import random
import time
import threading
import math
from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .agents import Bacteria, Phagocyte, Agent, Glucose
from .genetic_algorithm import GeneticAlgorithmDEAP as GeneticAlgorithm
from config import SimulationConfig

@dataclass
class Simulation:
    """Clase principal de simulación"""
    
    # Parámetros de simulación
    canvas_width: int = SimulationConfig.CANVAS_WIDTH
    canvas_height: int = SimulationConfig.CANVAS_HEIGHT
    background_color: Tuple[int, int, int] = SimulationConfig.BACKGROUND_COLOR
    max_generations: int = SimulationConfig.MAX_GENERATIONS
    
    # Poblaciones
    bacteria: List[Bacteria] = field(default_factory=list)
    phagocytes: List[Phagocyte] = field(default_factory=list)
    glucose: List[Glucose] = field(default_factory=list)
    
    # Algoritmo genético
    ga: GeneticAlgorithm = field(default_factory=GeneticAlgorithm)
    
    # Estado de simulación
    generation: int = 0
    is_paused: bool = False
    is_stopped: bool = False
    start_time: float = field(default_factory=time.time)
    
    # Estadísticas
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Inicializar después de la creación"""
        self.stats = {
            'total_captures': 0,
            'total_reproductions': 0,
            'glucose_consumed': 0,
            'max_fitness_history': {'bacteria': [], 'phagocytes': []},
            'avg_fitness_history': {'bacteria': [], 'phagocytes': []},
            'population_history': {'bacteria': [], 'phagocytes': [], 'glucose': []},
            'interaction_history': [],
            'generation_times': []
        }
        
        # Sistema de ranking
        self.bacteria_rankings = []
        self.last_ranking_update = 0
        self.ranking_update_frequency = SimulationConfig.RANKING_UPDATE_FREQUENCY
        
        if not self.glucose:
            self.initialize_glucose()
        # Inicializar poblaciones si están vacías
        if not self.bacteria:
            self.initialize_population()
    
    # En simulation.py, actualizar el método update_bacteria_rankings

    def update_bacteria_rankings(self):
        """Actualizar y ordenar lista de bacterias por vulnerabilidad"""
        # Calcular vulnerabilidad solo para objetos Bacteria
        vulnerability_scores = []
        for bacteria in self.bacteria:
            if bacteria.is_alive() and isinstance(bacteria, Bacteria) and hasattr(bacteria, 'get_vulnerability_score'):
                try:
                    score = bacteria.get_vulnerability_score(self.background_color)
                    vulnerability_scores.append((score, bacteria))
                except Exception as e:
                    print(f"Error calculando vulnerabilidad: {e}")
                    continue
        
        # Ordenar por vulnerabilidad descendente (mayor = más vulnerable)
        vulnerability_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Guardar solo las bacterias, sin los scores
        self.bacteria_rankings = [bacteria for _, bacteria in vulnerability_scores]
        self.last_ranking_update = self.generation
        
        # Registrar estadísticas de ranking
        if vulnerability_scores:
            scores = [score for score, _ in vulnerability_scores]
            if 'ranking_stats' not in self.stats:
                self.stats['ranking_stats'] = {'max_vulnerability': [], 'avg_vulnerability': []}
            
            self.stats['ranking_stats']['max_vulnerability'].append(max(scores))
            self.stats['ranking_stats']['avg_vulnerability'].append(np.mean(scores))
            
            # Mantener historial limitado
            max_history = 100
            for key in self.stats['ranking_stats']:
                if len(self.stats['ranking_stats'][key]) > max_history:
                    self.stats['ranking_stats'][key].pop(0)
    
    def get_ranked_bacteria_in_range(self, phagocyte: Phagocyte, max_distance: float = None) -> List[Bacteria]:
        """Obtener bacterias rankeadas dentro del rango del fagocito"""
        if max_distance is None:
            max_distance = SimulationConfig.DETECTION_RADIUS
        
        # Actualizar rankings si es necesario
        if (self.generation - self.last_ranking_update) >= self.ranking_update_frequency:
            self.update_bacteria_rankings()
        
        # Buscar bacterias rankeadas dentro del rango
        ranked_in_range = []
        
        for bacteria in self.bacteria_rankings:
            if not bacteria.is_alive():
                continue
            
            # Calcular distancia
            dx = bacteria.x - phagocyte.x
            dy = bacteria.y - phagocyte.y
            dist = math.sqrt(dx**2 + dy**2)
            
            # Verificar si está dentro del rango
            if dist < max_distance:
                # Verificar si el fagocito puede detectarla
                if phagocyte.detect_bacteria(bacteria, self.background_color):
                    ranked_in_range.append((dist, bacteria))
        
        # Ordenar por distancia para priorizar las más cercanas entre igualmente vulnerables
        ranked_in_range.sort(key=lambda x: x[0])
        
        return [bacteria for _, bacteria in ranked_in_range]
    
    def initialize_population(self):
        """Inicializar poblaciones iniciales"""
        print(f"Inicializando poblaciones con modo spawn: {SimulationConfig.PHAGOCYTE_SPAWN_MODE}")
        
        # Crear bacterias iniciales (siempre aleatorias)
        for i in range(SimulationConfig.INITIAL_BACTERIA_COUNT):
            bacteria = Bacteria(id=f"bacteria_{i}")
            bacteria.x = random.uniform(0, self.canvas_width)
            bacteria.y = random.uniform(0, self.canvas_height)
            self.bacteria.append(bacteria)
        
        # Crear fagocitos iniciales según el modo
        spawn_mode = SimulationConfig.PHAGOCYTE_SPAWN_MODE
        
        if spawn_mode == 'fixed_point':
            # Calcular punto de spawn relativo al tamaño actual del canvas
            spawn_x = self.canvas_width * (SimulationConfig.PHAGOCYTE_SPAWN_POINT[0] / SimulationConfig.CANVAS_WIDTH)
            spawn_y = self.canvas_height * (SimulationConfig.PHAGOCYTE_SPAWN_POINT[1] / SimulationConfig.CANVAS_HEIGHT)
            
            print(f"  Punto de spawn fagocitos: ({spawn_x:.0f}, {spawn_y:.0f})")
            print(f"  Radio de dispersión: {SimulationConfig.PHAGOCYTE_SPAWN_RADIUS}")
            
            for i in range(SimulationConfig.INITIAL_PHAGOCYTE_COUNT):
                phagocyte = Phagocyte(
                    id=f"phagocyte_{i}",
                    spawn_point=(spawn_x, spawn_y)  # Pasar punto de spawn
                )
                self.phagocytes.append(phagocyte)
        else:
            # Modo aleatorio tradicional
            for i in range(SimulationConfig.INITIAL_PHAGOCYTE_COUNT):
                phagocyte = Phagocyte(id=f"phagocyte_{i}")
                phagocyte.x = random.uniform(0, self.canvas_width)
                phagocyte.y = random.uniform(0, self.canvas_height)
                self.phagocytes.append(phagocyte)

    def initialize_glucose(self):
        """Inicializar glucosas iniciales"""
        for i in range(SimulationConfig.INITIAL_GLUCOSE_COUNT):
            glucose = Glucose(id=f"glucose_{i}")
            self.glucose.append(glucose)
        
        print(f"Inicializadas {len(self.glucose)} glucosas")
    
    # Añadir nuevo método para manejar glucosas
    def manage_glucose(self):
        """Gestionar ciclo de vida de glucosas"""
        # Eliminar glucosas consumidas
        active_glucose = [g for g in self.glucose if g.is_active()]
        self.glucose = active_glucose
        
        # Spawnear nuevas glucosas si es necesario
        if (len(self.glucose) < SimulationConfig.GLUCOSE_RESPAWN_THRESHOLD and 
            random.random() < SimulationConfig.GLUCOSE_SPAWN_RATE and
            len(self.glucose) < SimulationConfig.MAX_GLUCOSE_COUNT):
            
            new_glucose = Glucose()
            self.glucose.append(new_glucose)
    
    def clean_incorrect_agents(self):
        """Eliminar agentes que no son del tipo correcto"""
        # Filtrar bacterias que no son Bacteria
        self.bacteria = [b for b in self.bacteria if isinstance(b, Bacteria)]
        
        # Filtrar fagocitos que no son Phagocyte
        self.phagocytes = [p for p in self.phagocytes if isinstance(p, Phagocyte)]
            
    def step(self):
        """Ejecutar un paso de simulación (una generación)"""
        if self.is_paused or self.is_stopped:
            return
        
        start_gen_time = time.time()
        self.generation += 1
        
        try:
            # 1. Mover todos los agentes
            self.move_agents()

            # 1b. Actualizar cooldowns de reproducción (NUEVO)
            self.update_reproduction_cooldowns()
            
            # 2. Procesar interacciones
            self.process_interactions()
            
            # 2b. Gestionar glucosas
            self.manage_glucose()
            
            # 3. Calcular fitness
            self.calculate_fitness()
            
            # 4. Reproducción natural
            self.asexual_reproduction()
            
            # 5. Evolución coevolutiva (cada ciertas generaciones)
            if self.generation % SimulationConfig.GENERATIONS_PER_EPOCH == 0:
                self.coevolution_step()
            
            # 6. Limpiar agentes muertos
            self.clean_dead_agents()
            
            # 7. Limpiar agentes del tipo incorrecto (NUEVO)
            self.clean_incorrect_agents()
            
            # 8. Actualizar estadísticas
            self.update_statistics(start_gen_time)
            
            # 9. Controlar tamaño de población
            self.control_population_size()
            
        except Exception as e:
            print(f"Error en paso de simulación (generación {self.generation}): {e}")
            import traceback
            traceback.print_exc()
            
    def move_agents(self):
        """Mover todos los agentes en el entorno"""
        # Mover bacterias
        for bacteria in self.bacteria:
            if bacteria.is_alive():
                bacteria.move(self.canvas_width, self.canvas_height)
        
        # Mover fagocitos con búsqueda inteligente
        for phagocyte in self.phagocytes:
            if phagocyte.is_alive():
                # Pasar referencia a la simulación para acceso a rankings
                if hasattr(phagocyte, 'move'):
                    phagocyte.move(self.canvas_width, self.canvas_height, self)

    def update_reproduction_cooldowns(self):
        """Actualizar tiempos de enfriamiento para reproducción"""
        for bacteria in self.bacteria:
            if isinstance(bacteria, Bacteria) and hasattr(bacteria, 'update_reproduction_cooldown'):
                bacteria.update_reproduction_cooldown()
    
    def process_interactions(self):
        """Procesar interacciones entre agentes"""
        captures = 0
        glucose_consumed = 0
        
        # Para cada fagocito, verificar capturas
        for phagocyte in self.phagocytes:
            if not phagocyte.is_alive():
                continue
            
            # Verificar que sea un Phagocyte
            if not hasattr(phagocyte, 'capture_bacteria'):
                continue
            
            # Buscar bacterias cercanas para capturar
            for bacteria in self.bacteria[:]:  # Copia para modificar durante iteración
                if not bacteria.is_alive():
                    continue
                
                try:
                    if phagocyte.capture_bacteria(bacteria):
                        # Bacteria capturada
                        self.bacteria.remove(bacteria)
                        captures += 1
                except Exception as e:
                    print(f"Error capturando bacteria: {e}")
                    continue
        
        for bacteria in self.bacteria:
            if not bacteria.is_alive():
                continue
            
            # Buscar glucosas cercanas
            for glucose in self.glucose[:]:  # Copia para modificar
                if not glucose.is_active():
                    continue
                
                # Calcular distancia
                dx = bacteria.x - glucose.x
                dy = bacteria.y - glucose.y
                dist = math.sqrt(dx**2 + dy**2)
                
                # Radio de consumo (tamaño de bacteria + tamaño de glucosa)
                consumption_radius = SimulationConfig.AGENT_SIZE + (glucose.size / 2)
                
                if dist < consumption_radius:
                    # Bacteria consume glucosa
                    energy_gained = glucose.consume(SimulationConfig.BACTERIA_GLUCOSE_CONSUMPTION_RATE)
                    bacteria.energy += energy_gained
                    bacteria.energy = min(200.0, bacteria.energy)
                    glucose_consumed += 1
                    
                    # Registrar en estadísticas
                    self.stats['glucose_consumed'] += 1
                    
                    # Si la glucosa fue completamente consumida, eliminarla
                    if not glucose.is_active():
                        self.glucose.remove(glucose)
                    
                    # Una bacteria solo consume una glucosa por paso
                    break
        
        # Actualizar estadísticas
        self.stats['total_captures'] += captures
    
    def calculate_fitness(self):
        """Calcular fitness para todos los agentes"""
        # Fitness para bacterias (basado en camuflaje)
        for bacteria in self.bacteria:
            try:
                bacteria.calculate_fitness(self.background_color)
            except Exception as e:
                print(f"Error calculando fitness de bacteria: {e}")
                bacteria.fitness = 0.5  # Valor por defecto
        
        # Fitness para fagocitos (basado en éxito de caza y sensibilidad)
        for phagocyte in self.phagocytes:
            try:
                if hasattr(phagocyte, 'calculate_fitness'):
                    phagocyte.calculate_fitness(self.background_color, self.bacteria)
                else:
                    phagocyte.fitness = 0.5  # Valor por defecto
            except Exception as e:
                print(f"Error calculando fitness de fagocito: {e}")
                phagocyte.fitness = 0.5  # Valor por defecto
    
    def asexual_reproduction(self):
        """Reproducción asexual de bacterias"""
        new_bacteria = []
        
        for bacteria in self.bacteria[:]:  # Copia para iteración segura
            if not isinstance(bacteria, Bacteria):
                continue
            
            if not bacteria.is_alive():
                continue
            
            # Verificar si puede reproducirse
            if hasattr(bacteria, 'can_reproduce_asexually') and bacteria.can_reproduce_asexually():
                try:
                    child = bacteria.reproduce_asexually()
                    if child:
                        new_bacteria.append(child)
                        self.stats['total_reproductions'] += 1
                        
                        # Registrar en historial
                        if 'asexual_reproductions' not in self.stats:
                            self.stats['asexual_reproductions'] = []
                        
                        self.stats['asexual_reproductions'].append({
                            'generation': self.generation,
                            'parent_id': bacteria.id,
                            'child_id': child.id,
                            'parent_energy': bacteria.energy,
                            'parent_fitness': bacteria.fitness
                        })
                        
                        # Mantener historial limitado
                        max_history = 100
                        if len(self.stats['asexual_reproductions']) > max_history:
                            self.stats['asexual_reproductions'].pop(0)
                        
                except Exception as e:
                    print(f"Error en reproducción asexual de bacteria {bacteria.id}: {e}")
                    continue
        
        # Agregar nuevas bacterias a la población
        self.bacteria.extend(new_bacteria)
        
        # Registrar estadística
        if new_bacteria:
            if 'asexual_reproduction_count' not in self.stats:
                self.stats['asexual_reproduction_count'] = 0
            self.stats['asexual_reproduction_count'] += len(new_bacteria)
    
    def coevolution_step(self):
        """Paso de evolución coevolutiva usando algoritmo genético"""
        try:
            # Evolucionar ambas poblaciones
            self.bacteria, self.phagocytes = self.ga.evolve_population(  # CAMBIA AQUÍ
                self.bacteria,
                self.phagocytes,
                self.background_color
            )
            
            # Reposicionar agentes después de evolución
            for agent in self.bacteria + self.phagocytes:
                agent.x = random.uniform(0, self.canvas_width)
                agent.y = random.uniform(0, self.canvas_height)
                agent.energy = 100.0  # Resetear energía
                agent.age = 0  # Resetear edad
                
        except Exception as e:
            print(f"Error en paso coevolutivo: {e}")
            import traceback
            traceback.print_exc()
    
    def clean_dead_agents(self):
        """Eliminar agentes muertos"""
        # Limpiar bacterias muertas
        self.bacteria = [b for b in self.bacteria if b.is_alive()]
        
        # Limpiar fagocitos muertos
        self.phagocytes = [p for p in self.phagocytes if p.is_alive()]
    
    def update_statistics(self, start_time: float):
        """Actualizar estadísticas de simulación"""
        # Calcular tiempos
        gen_time = time.time() - start_time
        self.stats['generation_times'].append(gen_time)
        
        # Mantener historial limitado
        if len(self.stats['generation_times']) > 100:
            self.stats['generation_times'].pop(0)
        
        # Filtrar solo objetos Bacteria reales
        real_bacteria = [b for b in self.bacteria if isinstance(b, Bacteria)]
        
        # Calcular fitness para bacterias reales
        if real_bacteria:
            try:
                bact_fitness = [b.fitness for b in real_bacteria]
                self.stats['max_fitness_history']['bacteria'].append(max(bact_fitness))
                self.stats['avg_fitness_history']['bacteria'].append(np.mean(bact_fitness))
                
                # Calcular vulnerabilidad promedio solo para Bacteria reales
                vulnerabilities = []
                for b in real_bacteria:
                    if hasattr(b, 'get_vulnerability_score'):
                        try:
                            vulnerabilities.append(b.get_vulnerability_score(self.background_color))
                        except Exception as e:
                            print(f"Error calculando vulnerabilidad en stats: {e}")
                            continue
                
                if vulnerabilities:
                    if 'vulnerability_stats' not in self.stats:
                        self.stats['vulnerability_stats'] = {'avg': [], 'max': [], 'min': []}
                    
                    self.stats['vulnerability_stats']['avg'].append(np.mean(vulnerabilities))
                    self.stats['vulnerability_stats']['max'].append(max(vulnerabilities))
                    self.stats['vulnerability_stats']['min'].append(min(vulnerabilities))
                    
                    # Mantener historial limitado
                    max_history = 100
                    for key in ['avg', 'max', 'min']:
                        if len(self.stats['vulnerability_stats'][key]) > max_history:
                            self.stats['vulnerability_stats'][key].pop(0)
                            
            except Exception as e:
                print(f"Error calculando estadísticas de bacteria: {e}")
                self.stats['max_fitness_history']['bacteria'].append(0.0)
                self.stats['avg_fitness_history']['bacteria'].append(0.0)
        else:
            self.stats['max_fitness_history']['bacteria'].append(0.0)
            self.stats['avg_fitness_history']['bacteria'].append(0.0)
        
        # Filtrar solo objetos Phagocyte reales
        real_phagocytes = [p for p in self.phagocytes if isinstance(p, Phagocyte)]
        
        # Calcular fitness para fagocitos reales
        if real_phagocytes:
            try:
                phag_fitness = [p.fitness for p in real_phagocytes]
                self.stats['max_fitness_history']['phagocytes'].append(max(phag_fitness))
                self.stats['avg_fitness_history']['phagocytes'].append(np.mean(phag_fitness))
            except:
                self.stats['max_fitness_history']['phagocytes'].append(0.0)
                self.stats['avg_fitness_history']['phagocytes'].append(0.0)
        else:
            self.stats['max_fitness_history']['phagocytes'].append(0.0)
            self.stats['avg_fitness_history']['phagocytes'].append(0.0)
        
        # Actualizar poblaciones
        self.stats['population_history']['bacteria'].append(len(real_bacteria))
        self.stats['population_history']['phagocytes'].append(len(real_phagocytes))
        
        # Mantener historial limitado
        max_history = 100
        for key in ['bacteria', 'phagocytes']:
            if len(self.stats['max_fitness_history'][key]) > max_history:
                self.stats['max_fitness_history'][key].pop(0)
            if len(self.stats['avg_fitness_history'][key]) > max_history:
                self.stats['avg_fitness_history'][key].pop(0)
            if len(self.stats['population_history'][key]) > max_history:
                self.stats['population_history'][key].pop(0)
    




    def control_population_size(self):
        """Controlar tamaño de población para evitar explosión"""
        max_pop = SimulationConfig.MAX_POPULATION
        
        # Limitar bacterias
        if len(self.bacteria) > max_pop:
            # Eliminar las bacterias con menor fitness
            try:
                self.bacteria.sort(key=lambda b: b.fitness, reverse=True)
                self.bacteria = self.bacteria[:max_pop]
            except:
                # Si hay error, tomar una muestra aleatoria
                self.bacteria = random.sample(self.bacteria, min(max_pop, len(self.bacteria)))
        
        # Limitar fagocitos
        if len(self.phagocytes) > max_pop // 2:
            try:
                self.phagocytes.sort(key=lambda p: p.fitness, reverse=True)
                self.phagocytes = self.phagocytes[:max_pop // 2]
            except:
                # Si hay error, tomar una muestra aleatoria
                self.phagocytes = random.sample(self.phagocytes, min(max_pop // 2, len(self.phagocytes)))
    
    def update_parameters(self, parameters: Dict[str, Any]):
        """Actualizar parámetros de simulación"""
        # Actualizar configuración de simulación
        if 'canvas_width' in parameters:
            self.canvas_width = int(parameters['canvas_width'])
        if 'canvas_height' in parameters:
            self.canvas_height = int(parameters['canvas_height'])
        if 'background_color' in parameters:
            self.background_color = tuple(parameters['background_color'])
        if 'max_generations' in parameters:
            self.max_generations = int(parameters['max_generations'])
        
        # Actualizar sistema de spawn
        if 'phagocyte_spawn_mode' in parameters:
            SimulationConfig.PHAGOCYTE_SPAWN_MODE = parameters['phagocyte_spawn_mode']
        if 'phagocyte_spawn_point' in parameters:
            SimulationConfig.PHAGOCYTE_SPAWN_POINT = tuple(parameters['phagocyte_spawn_point'])
        if 'phagocyte_spawn_radius' in parameters:
            SimulationConfig.PHAGOCYTE_SPAWN_RADIUS = float(parameters['phagocyte_spawn_radius'])
        
        # Actualizar sistema de ranking
        if 'ranking_update_frequency' in parameters:
            self.ranking_update_frequency = int(parameters['ranking_update_frequency'])
        
        # Actualizar algoritmo genético
        ga_params = {}
        if 'mutation_rate' in parameters:
            ga_params['mutation_rate'] = float(parameters['mutation_rate'])
        if 'crossover_rate' in parameters:
            ga_params['crossover_rate'] = float(parameters['crossover_rate'])
        if 'mutation_strength' in parameters:
            ga_params['mutation_strength'] = float(parameters['mutation_strength'])
        
        if ga_params:
            self.ga.update_parameters(**ga_params)
    
    # En simulation.py, corregir el método get_simulation_state (línea ~547)

    def get_simulation_state(self) -> Dict[str, Any]:
        """Obtener estado completo de simulación para enviar al cliente"""
        # Limitar número de agentes para optimizar transferencia
        max_bacteria_show = 200
        max_phagocytes_show = 50
        max_glucose_show = 50
        glucose_to_show = self.glucose[:max_glucose_show]
        
        # Seleccionar agentes para mostrar - AÑADIR FILTRO POR TIPO
        bacteria_to_show = [b for b in self.bacteria if isinstance(b, Bacteria)][:max_bacteria_show]
        phagocytes_to_show = [p for p in self.phagocytes if isinstance(p, Phagocyte)][:max_phagocytes_show]
        
        # Si hay muchos agentes, muestrear aleatoriamente
        if len([b for b in self.bacteria if isinstance(b, Bacteria)]) > max_bacteria_show:
            real_bacteria = [b for b in self.bacteria if isinstance(b, Bacteria)]
            bacteria_to_show = random.sample(real_bacteria, max_bacteria_show)
        
        if len([p for p in self.phagocytes if isinstance(p, Phagocyte)]) > max_phagocytes_show:
            real_phagocytes = [p for p in self.phagocytes if isinstance(p, Phagocyte)]
            phagocytes_to_show = random.sample(real_phagocytes, max_phagocytes_show)
        
        # Convertir bacterias a diccionario
        bacteria_data = []
        for b in bacteria_to_show:
            try:
                # Asegurarnos de que sea una Bacteria y tenga el método
                if isinstance(b, Bacteria) and hasattr(b, 'get_vulnerability_score'):
                    bacteria_data.append({
                        'id': b.id,
                        'x': b.x,
                        'y': b.y,
                        'can_reproduce' : b.can_reproduce_asexually() if hasattr(b, 'can_reproduce_asexually') else False,
                        'reproduction_cooldown': getattr(b, 'reproduction_cooldown', 0),
                        'offspring_count': getattr(b, 'offspring_count', 0),
                        'parent_id': getattr(b, 'parent_id', None),
                        'color': b.color,
                        'fitness': b.fitness,
                        'energy': b.energy,
                        'age': b.age,
                        'genome': b.genome,
                        'vx': getattr(b, 'vx', 0),
                        'vy': getattr(b, 'vy', 0),
                        'direction': getattr(b, 'direction', 0),
                        'length_gene': b.genome.get('length_gene', 0.5),
                        'width_gene': b.genome.get('width_gene', 0.5),
                        'vulnerability': b.get_vulnerability_score(self.background_color)
                    })
            except Exception as e:
                print(f"Error serializando bacteria: {e}")
                continue
        
        # Convertir fagocitos a diccionario
        phagocytes_data = []
        for p in phagocytes_to_show:
            try:
                if isinstance(p, Phagocyte):
                    phagocytes_data.append({
                        'id': p.id,
                        'x': p.x,
                        'y': p.y,
                        'color': p.color,
                        'fitness': p.fitness,
                        'energy': p.energy,
                        'age': p.age,
                        'genome': p.genome,
                        'vx': getattr(p, 'vx', 0),
                        'vy': getattr(p, 'vy', 0),
                        'aggression_gene': p.genome.get('aggression_gene', 0.5),
                        'sensitivity_gene': p.genome.get('sensitivity_gene', 0.5)
                    })
            except Exception as e:
                print(f"Error serializando fagocito: {e}")
                continue
        
        # Convertir glucosas a diccionario
        glucose_data = []
        for g in glucose_to_show:
            try:
                if isinstance(g, Glucose):
                    glucose_data.append({
                        'id': g.id,
                        'x': g.x,
                        'y': g.y,
                        'size': g.size,
                        'energy': g.energy,
                        'consumed': g.consumed
                    })
            except Exception as e:
                print(f"Error serializando glucosa: {e}")
                continue

        # Calcular estadísticas solo para objetos del tipo correcto
        real_bacteria = [b for b in self.bacteria if isinstance(b, Bacteria)]
        real_phagocytes = [p for p in self.phagocytes if isinstance(p, Phagocyte)]
        
        # Calcular estadísticas de reproducción
        reproduction_stats = {
            'total_asexual': self.stats.get('asexual_reproduction_count', 0),
            'can_reproduce_now': sum(1 for b in real_bacteria 
                                    if hasattr(b, 'can_reproduce_asexually') 
                                    and b.can_reproduce_asexually()),
            'average_offspring': np.mean([b.offspring_count for b in real_bacteria]) 
                                if real_bacteria else 0
        }

        return {
            'generation': self.generation,
            'timestamp': datetime.now().isoformat(),
            'agents': {
                'bacteria': bacteria_data,
                'phagocytes': phagocytes_data,
                'glucose': glucose_data
            },
            'stats': {
                'populations': {
                    'bacteria': len(real_bacteria),
                    'phagocytes': len(real_phagocytes),
                    'glucose': len(self.glucose)
                },
                'reproduction': {
                    'total_asexual': self.stats.get('asexual_reproduction_count', 0),
                    'can_reproduce_now': sum(1 for b in real_bacteria 
                                            if hasattr(b, 'can_reproduce_asexually') 
                                            and b.can_reproduce_asexually()),
                    'average_offspring': np.mean([b.offspring_count for b in real_bacteria]) 
                                        if real_bacteria else 0
                },
                'fitness': {
                    'bacteria': {
                        'max': max([b.fitness for b in real_bacteria]) if real_bacteria else 0.0,
                        'avg': np.mean([b.fitness for b in real_bacteria]) if real_bacteria else 0.0,
                        'min': min([b.fitness for b in real_bacteria]) if real_bacteria else 0.0
                    },
                    'phagocytes': {
                        'max': max([p.fitness for p in real_phagocytes]) if real_phagocytes else 0.0,
                        'avg': np.mean([p.fitness for p in real_phagocytes]) if real_phagocytes else 0.0,
                        'min': min([p.fitness for p in real_phagocytes]) if real_phagocytes else 0.0
                    }
                },
                'vulnerability': {
                    'max': max([b.get_vulnerability_score(self.background_color) for b in real_bacteria]) if real_bacteria else 0.0,
                    'avg': np.mean([b.get_vulnerability_score(self.background_color) for b in real_bacteria]) if real_bacteria else 0.0,
                    'min': min([b.get_vulnerability_score(self.background_color) for b in real_bacteria]) if real_bacteria else 0.0
                } if real_bacteria else {'max': 0.0, 'avg': 0.0, 'min': 0.0},
                'captures': self.stats['total_captures'],
                'reproductions': self.stats['total_reproductions'],
                'glucose_consumed': self.stats['glucose_consumed']
            },
            'parameters': self.get_parameters(),
            'environment': {
                'width': self.canvas_width,
                'height': self.canvas_height,
                'background_color': self.background_color
            }
        }
    
    def get_parameters(self) -> Dict[str, Any]:
        """Obtener parámetros actuales de simulación"""
        return {
            'canvas_width': self.canvas_width,
            'canvas_height': self.canvas_height,
            'background_color': self.background_color,
            'max_generations': self.max_generations,
            'mutation_rate': self.ga.mutation_rate,
            'crossover_rate': self.ga.crossover_rate,
            'mutation_strength': self.ga.mutation_strength,
            'phagocyte_spawn_mode': SimulationConfig.PHAGOCYTE_SPAWN_MODE,
            'phagocyte_spawn_point': SimulationConfig.PHAGOCYTE_SPAWN_POINT,
            'phagocyte_spawn_radius': SimulationConfig.PHAGOCYTE_SPAWN_RADIUS,
            'ranking_update_frequency': self.ranking_update_frequency,
            'current_generation': self.generation,
            'bacteria_count': len(self.bacteria),
            'phagocyte_count': len(self.phagocytes)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas detalladas"""
        current_time = time.time()
        
        stats = {
            'summary': {
                'total_generations': self.generation,
                'total_captures': self.stats['total_captures'],
                'total_reproductions': self.stats['total_reproductions'],
                'current_population': {
                    'bacteria': len(self.bacteria),
                    'phagocytes': len(self.phagocytes)
                },
                'run_time': current_time - self.start_time
            },
            'fitness_history': {
                'max': self.stats['max_fitness_history'],
                'avg': self.stats['avg_fitness_history']
            },
            'population_history': self.stats['population_history'],
            'performance': {
                'avg_generation_time': np.mean(self.stats['generation_times']) if self.stats['generation_times'] else 0.0,
                'fps': 1.0 / np.mean(self.stats['generation_times']) if self.stats['generation_times'] and np.mean(self.stats['generation_times']) > 0 else 0.0,
                'generation_times': self.stats['generation_times'][-10:] if self.stats['generation_times'] else []
            }
        }
        
        # Agregar estadísticas de vulnerabilidad si existen
        if 'vulnerability_stats' in self.stats:
            stats['vulnerability_history'] = self.stats['vulnerability_stats']
        
        # Agregar estadísticas de ranking si existen
        if 'ranking_stats' in self.stats:
            stats['ranking_history'] = self.stats['ranking_stats']
        
        return stats
    
    def get_best_fitness(self) -> Dict[str, float]:
        """Obtener mejor fitness de cada especie"""
        return {
            'bacteria': max([b.fitness for b in self.bacteria]) if self.bacteria else 0.0,
            'phagocytes': max([p.fitness for p in self.phagocytes]) if self.phagocytes else 0.0
        }
    
    def get_average_fitness(self) -> Dict[str, float]:
        """Obtener fitness promedio de cada especie"""
        return {
            'bacteria': np.mean([b.fitness for b in self.bacteria]) if self.bacteria else 0.0,
            'phagocytes': np.mean([p.fitness for p in self.phagocytes]) if self.phagocytes else 0.0
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado general de simulación"""
        return {
            'is_running': not self.is_paused and not self.is_stopped,
            'is_paused': self.is_paused,
            'generation': self.generation,
            'population': {
                'bacteria': len(self.bacteria),
                'phagocytes': len(self.phagocytes)
            },
            'run_time': time.time() - self.start_time,
            'timestamp': datetime.now().isoformat(),
            'ranking_info': {
                'last_update': self.last_ranking_update,
                'current_ranking_size': len(self.bacteria_rankings),
                'update_frequency': self.ranking_update_frequency
            }
        }
    
    def pause(self):
        """Pausar simulación"""
        self.is_paused = True
    
    def resume(self):
        """Reanudar simulación"""
        self.is_paused = False
    
    def reset(self):
        """Reiniciar simulación"""
        self.generation = 0
        self.is_paused = False
        self.is_stopped = False
        self.start_time = time.time()
        self.stats = {
            'total_captures': 0,
            'total_reproductions': 0,
            'max_fitness_history': {'bacteria': [], 'phagocytes': []},
            'avg_fitness_history': {'bacteria': [], 'phagocytes': []},
            'population_history': {'bacteria': [], 'phagocytes': []},
            'interaction_history': [],
            'generation_times': []
        }
        
        # Reiniciar sistema de ranking
        self.bacteria_rankings = []
        self.last_ranking_update = 0
        
        # Reiniciar poblaciones
        self.bacteria = []
        self.phagocytes = []
        self.initialize_population()
    
    def stop(self):
        """Detener simulación completamente"""
        self.is_stopped = True
        self.is_paused = True