"""
Clase principal de simulación
"""
import numpy as np
import random
import time
import threading
from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .agents import Bacteria, Phagocyte, Agent
from .genetic_algorithm import GeneticAlgorithm
from .fitness import calculate_coevolution_fitness
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
            'max_fitness_history': {'bacteria': [], 'phagocytes': []},
            'avg_fitness_history': {'bacteria': [], 'phagocytes': []},
            'population_history': {'bacteria': [], 'phagocytes': []},
            'interaction_history': [],
            'generation_times': []
        }
        
        # Inicializar poblaciones si están vacías
        if not self.bacteria:
            self.initialize_population()
    
    def initialize_population(self):
        """Inicializar poblaciones iniciales"""
        # Crear bacterias iniciales
        for i in range(SimulationConfig.INITIAL_BACTERIA_COUNT):
            bacteria = Bacteria(id=f"bacteria_{i}")
            bacteria.x = random.uniform(0, self.canvas_width)
            bacteria.y = random.uniform(0, self.canvas_height)
            self.bacteria.append(bacteria)
        
        # Crear fagocitos iniciales
        for i in range(SimulationConfig.INITIAL_PHAGOCYTE_COUNT):
            phagocyte = Phagocyte(id=f"phagocyte_{i}")
            phagocyte.x = random.uniform(0, self.canvas_width)
            phagocyte.y = random.uniform(0, self.canvas_height)
            self.phagocytes.append(phagocyte)
    
    def step(self):
        """Ejecutar un paso de simulación (una generación)"""
        if self.is_paused or self.is_stopped:
            return
        
        start_gen_time = time.time()
        self.generation += 1
        
        try:
            # 1. Mover todos los agentes
            self.move_agents()
            
            # 2. Procesar interacciones
            self.process_interactions()
            
            # 3. Calcular fitness
            self.calculate_fitness()
            
            # 4. Reproducción natural
            self.natural_reproduction()
            
            # 5. Evolución coevolutiva (cada ciertas generaciones)
            if self.generation % SimulationConfig.GENERATIONS_PER_EPOCH == 0:
                self.coevolution_step()
            
            # 6. Limpiar agentes muertos
            self.clean_dead_agents()
            
            # 7. Actualizar estadísticas
            self.update_statistics(start_gen_time)
            
            # 8. Controlar tamaño de población
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
        
        # Mover fagocitos
        for phagocyte in self.phagocytes:
            if phagocyte.is_alive():
                # Verificar que sea un Phagocyte y tenga los métodos necesarios
                if hasattr(phagocyte, 'detect_bacteria') and hasattr(phagocyte, 'chase_bacteria'):
                    try:
                        # Buscar bacterias cercanas para perseguir
                        target_bacteria = self.find_nearest_bacteria(phagocyte)
                        if target_bacteria:
                            phagocyte.chase_bacteria(target_bacteria)
                    except Exception as e:
                        print(f"Error persiguiendo bacterias: {e}")
                        # Continuar con el movimiento incluso si hay error
                
                phagocyte.move(self.canvas_width, self.canvas_height)
    
    def find_nearest_bacteria(self, phagocyte: Phagocyte, 
                            max_distance: float = None) -> Optional[Bacteria]:
        """Encontrar bacteria más cercana detectable"""
        if max_distance is None:
            max_distance = SimulationConfig.DETECTION_RADIUS
        
        # Verificar que el fagocito tenga el método detect_bacteria
        if not hasattr(phagocyte, 'detect_bacteria'):
            return None
        
        nearest = None
        min_dist = float('inf')
        
        for bacteria in self.bacteria:
            if not bacteria.is_alive():
                continue
            
            # Calcular distancia
            dx = bacteria.x - phagocyte.x
            dy = bacteria.y - phagocyte.y
            dist = np.sqrt(dx**2 + dy**2)
            
            # Verificar si está dentro del rango y es detectable
            if dist < max_distance and dist < min_dist:
                try:
                    if phagocyte.detect_bacteria(bacteria, self.background_color):
                        nearest = bacteria
                        min_dist = dist
                except Exception as e:
                    print(f"Error detectando bacteria: {e}")
                    continue
        
        return nearest
    
    def process_interactions(self):
        """Procesar interacciones entre agentes"""
        captures = 0
        
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
    
    def natural_reproduction(self):
        """Reproducción natural dentro de la simulación"""
        new_bacteria = []
        new_phagocytes = []
        
        # Reproducción de bacterias
        for bacteria in self.bacteria[:]:  # Copia para iteración segura
            if bacteria.is_alive():
                try:
                    child = bacteria.reproduce()
                    if child:
                        new_bacteria.append(child)
                        self.stats['total_reproductions'] += 1
                except Exception as e:
                    print(f"Error reproduciendo bacteria: {e}")
                    continue
        
        # Reproducción de fagocitos
        for phagocyte in self.phagocytes[:]:  # Copia para iteración segura
            if phagocyte.is_alive():
                try:
                    if hasattr(phagocyte, 'reproduce'):
                        child = phagocyte.reproduce()
                        if child:
                            new_phagocytes.append(child)
                            self.stats['total_reproductions'] += 1
                except Exception as e:
                    print(f"Error reproduciendo fagocito: {e}")
                    continue
        
        # Agregar nuevos agentes a las poblaciones
        self.bacteria.extend(new_bacteria)
        self.phagocytes.extend(new_phagocytes)
    
    def coevolution_step(self):
        """Paso de evolución coevolutiva usando algoritmo genético"""
        try:
            # Evolucionar ambas poblaciones
            self.bacteria, self.phagocytes = self.ga.evolve_population(
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
        
        # Calcular fitness
        if self.bacteria:
            try:
                bact_fitness = [b.fitness for b in self.bacteria]
                self.stats['max_fitness_history']['bacteria'].append(max(bact_fitness))
                self.stats['avg_fitness_history']['bacteria'].append(np.mean(bact_fitness))
            except:
                self.stats['max_fitness_history']['bacteria'].append(0.0)
                self.stats['avg_fitness_history']['bacteria'].append(0.0)
        else:
            self.stats['max_fitness_history']['bacteria'].append(0.0)
            self.stats['avg_fitness_history']['bacteria'].append(0.0)
        
        if self.phagocytes:
            try:
                phag_fitness = [p.fitness for p in self.phagocytes]
                self.stats['max_fitness_history']['phagocytes'].append(max(phag_fitness))
                self.stats['avg_fitness_history']['phagocytes'].append(np.mean(phag_fitness))
            except:
                self.stats['max_fitness_history']['phagocytes'].append(0.0)
                self.stats['avg_fitness_history']['phagocytes'].append(0.0)
        else:
            self.stats['max_fitness_history']['phagocytes'].append(0.0)
            self.stats['avg_fitness_history']['phagocytes'].append(0.0)
        
        # Actualizar poblaciones
        self.stats['population_history']['bacteria'].append(len(self.bacteria))
        self.stats['population_history']['phagocytes'].append(len(self.phagocytes))
        
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
    
    def get_simulation_state(self) -> Dict[str, Any]:
        """Obtener estado completo de simulación para enviar al cliente"""
        # Limitar número de agentes para optimizar transferencia
        max_bacteria_show = 200
        max_phagocytes_show = 50
        
        # Seleccionar agentes para mostrar
        bacteria_to_show = self.bacteria[:max_bacteria_show]
        phagocytes_to_show = self.phagocytes[:max_phagocytes_show]
        
        # Si hay muchos agentes, muestrear aleatoriamente
        if len(self.bacteria) > max_bacteria_show:
            bacteria_to_show = random.sample(self.bacteria, max_bacteria_show)
        
        if len(self.phagocytes) > max_phagocytes_show:
            phagocytes_to_show = random.sample(self.phagocytes, max_phagocytes_show)
        
        # Convertir bacterias a diccionario
        bacteria_data = []
        for b in bacteria_to_show:
            try:
                bacteria_data.append({
                    'id': b.id,
                    'x': b.x,
                    'y': b.y,
                    'color': b.color,
                    'fitness': b.fitness,
                    'energy': b.energy,
                    'age': b.age,
                    'genome': b.genome,
                    'vx': getattr(b, 'vx', 0),
                    'vy': getattr(b, 'vy', 0),
                    'direction': getattr(b, 'direction', 0),
                    'length_gene': b.genome.get('length_gene', 0.5),
                    'width_gene': b.genome.get('width_gene', 0.5)
                })
            except Exception as e:
                print(f"Error serializando bacteria: {e}")
                continue
        
        # Convertir fagocitos a diccionario
        phagocytes_data = []
        for p in phagocytes_to_show:
            try:
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
                    'aggression_gene': p.genome.get('aggression_gene', 0.5)
                })
            except Exception as e:
                print(f"Error serializando fagocito: {e}")
                continue
        
        return {
            'generation': self.generation,
            'timestamp': datetime.now().isoformat(),
            'agents': {
                'bacteria': bacteria_data,
                'phagocytes': phagocytes_data
            },
            'stats': {
                'populations': {
                    'bacteria': len(self.bacteria),
                    'phagocytes': len(self.phagocytes)
                },
                'fitness': {
                    'bacteria': {
                        'max': max([b.fitness for b in self.bacteria]) if self.bacteria else 0.0,
                        'avg': np.mean([b.fitness for b in self.bacteria]) if self.bacteria else 0.0,
                        'min': min([b.fitness for b in self.bacteria]) if self.bacteria else 0.0
                    },
                    'phagocytes': {
                        'max': max([p.fitness for p in self.phagocytes]) if self.phagocytes else 0.0,
                        'avg': np.mean([p.fitness for p in self.phagocytes]) if self.phagocytes else 0.0,
                        'min': min([p.fitness for p in self.phagocytes]) if self.phagocytes else 0.0
                    }
                },
                'captures': self.stats['total_captures'],
                'reproductions': self.stats['total_reproductions']
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
            'current_generation': self.generation,
            'bacteria_count': len(self.bacteria),
            'phagocyte_count': len(self.phagocytes)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas detalladas"""
        current_time = time.time()
        
        return {
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
            'timestamp': datetime.now().isoformat()
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
        
        # Reiniciar poblaciones
        self.bacteria = []
        self.phagocytes = []
        self.initialize_population()
    
    def stop(self):
        """Detener simulación completamente"""
        self.is_stopped = True
        self.is_paused = True