"""
Configuración de la simulación
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, List

@dataclass
class SimulationConfig:
    """Configuración de la simulación"""
    
    # Dimensiones del entorno
    CANVAS_WIDTH: int = 800
    CANVAS_HEIGHT: int = 600
    
    # Parámetros de simulación
    FPS: int = 30
    BACKGROUND_COLOR: Tuple[int, int, int] = (240, 240, 240)
    MAX_GENERATIONS: int = 1000
    
    # Parámetros de población
    INITIAL_BACTERIA_COUNT: int = 100
    INITIAL_PHAGOCYTE_COUNT: int = 50
    MAX_POPULATION: int = 200
    
    # Parámetros genéticos
    MUTATION_RATE: float = 0.01
    CROSSOVER_RATE: float = 0.8
    MUTATION_STRENGTH: float = 0.1
    
    # Parámetros de movimiento
    MAX_SPEED: float = 2.0
    TURN_RATE: float = 0.1
    
    # Parámetros de interacción
    DETECTION_RADIUS: float = 50.0
    CAPTURE_RADIUS: float = 10.0
    ENERGY_GAIN: float = 10.0
    ENERGY_LOSS: float = 1.0
    
    # Coevolución
    GENERATIONS_PER_EPOCH: int = 50
    FITNESS_EPSILON: float = 0.01
    
    # Visualización
    AGENT_SIZE: float = 5.0
    PHAGOCYTE_SIZE: float = 8.0
    
    # Nuevos parámetros para formas
    BACILLUS_BASE_LENGTH: float = 12.0
    BACILLUS_BASE_WIDTH: float = 4.5
    PHAGOCYTE_BORDER_WIDTH: float = 3.0
    PHAGOCYTE_CENTER_RATIO: float = 0.6
    
    # Sistema de aparición de fagocitos
    PHAGOCYTE_SPAWN_MODE: str = 'fixed_point'  # 'random' o 'fixed_point'
    PHAGOCYTE_SPAWN_POINT: Tuple[float, float] = (800.0, 300.0)  # Centro del canvas
    PHAGOCYTE_SPAWN_RADIUS: float = 50.0  # Radio de dispersión inicial
    
    # Sistema de ranking
    RANKING_UPDATE_FREQUENCY: int = 5
    DETECTION_PRIORITY: str = 'vulnerability'  # 'vulnerability' o 'distance'
    
    # Parámetros de vulnerabilidad
    VULNERABILITY_COLOR_WEIGHT: float = 0.6  # Peso del color en vulnerabilidad
    VULNERABILITY_ENERGY_WEIGHT: float = 0.3  # Peso de la energía
    VULNERABILITY_AGE_WEIGHT: float = 0.1     # Peso de la edad

    # Parámetros DEAP
    DEAP_SELECTION_METHOD: str = 'tournament'  # 'tournament', 'roulette', 'best', 'random'
    DEAP_CROSSOVER_METHOD: str = 'uniform'     # 'uniform', 'onepoint', 'twopoint'
    DEAP_POPULATION_SIZE: int = 100
    DEAP_GENERATIONS: int = 10
    DEAP_HALL_OF_FAME_SIZE: int = 5

    # Parámetros de Glucosa
    INITIAL_GLUCOSE_COUNT: int = 30
    MAX_GLUCOSE_COUNT: int = 50
    GLUCOSE_SPAWN_RATE: float = 0.1  # Probabilidad de spawn por generación
    GLUCOSE_MIN_SIZE: float = 5.0
    GLUCOSE_MAX_SIZE: float = 20.0
    GLUCOSE_ENERGY_MULTIPLIER: float = 5.0  # Energía = tamaño × multiplicador
    BACTERIA_GLUCOSE_CONSUMPTION_RATE: float = 0.5  # Cuánta energía obtienen las bacterias
    GLUCOSE_RESPAWN_THRESHOLD: int = 10  # Mínimo de glucosas activas para spawnear nuevas

    # Parámetros de Reproducción Asexual
    BACTERIA_REPRODUCTION_ENERGY_THRESHOLD: float = 150.0  # Energía mínima para reproducirse
    BACTERIA_REPRODUCTION_ENERGY_COST: float = 75.0  # Energía que gasta al reproducirse
    BACTERIA_REPRODUCTION_COOLDOWN: int = 10  # Generaciones entre reproducciones
    BACTERIA_OFFSET_DISTANCE: float = 15.0  # Distancia de la bacteria hija
    BACTERIA_REPRODUCTION_MUTATION_RATE: float = 0.2  # Tasa de mutación en reproducción asexual


    @classmethod
    def get_default_parameters(cls) -> Dict[str, Any]:
        """Obtener parámetros por defecto como diccionario"""
        return {
            'canvas_width': cls.CANVAS_WIDTH,
            'canvas_height': cls.CANVAS_HEIGHT,
            'fps': cls.FPS,
            'background_color': cls.BACKGROUND_COLOR,
            'max_generations': cls.MAX_GENERATIONS,
            'initial_bacteria_count': cls.INITIAL_BACTERIA_COUNT,
            'initial_phagocyte_count': cls.INITIAL_PHAGOCYTE_COUNT,
            'max_population': cls.MAX_POPULATION,
            'mutation_rate': cls.MUTATION_RATE,
            'crossover_rate': cls.CROSSOVER_RATE,
            'mutation_strength': cls.MUTATION_STRENGTH,
            'max_speed': cls.MAX_SPEED,
            'turn_rate': cls.TURN_RATE,
            'detection_radius': cls.DETECTION_RADIUS,
            'capture_radius': cls.CAPTURE_RADIUS,
            'energy_gain': cls.ENERGY_GAIN,
            'energy_loss': cls.ENERGY_LOSS,
            'generations_per_epoch': cls.GENERATIONS_PER_EPOCH,
            'fitness_epsilon': cls.FITNESS_EPSILON,
            'agent_size': cls.AGENT_SIZE,
            'phagocyte_size': cls.PHAGOCYTE_SIZE,
            'bacillus_base_length': cls.BACILLUS_BASE_LENGTH,
            'bacillus_base_width': cls.BACILLUS_BASE_WIDTH,
            'phagocyte_border_width': cls.PHAGOCYTE_BORDER_WIDTH,
            'phagocyte_center_ratio': cls.PHAGOCYTE_CENTER_RATIO,
            'phagocyte_spawn_mode': cls.PHAGOCYTE_SPAWN_MODE,
            'phagocyte_spawn_point': cls.PHAGOCYTE_SPAWN_POINT,
            'phagocyte_spawn_radius': cls.PHAGOCYTE_SPAWN_RADIUS,
            'ranking_update_frequency': cls.RANKING_UPDATE_FREQUENCY,
            'detection_priority': cls.DETECTION_PRIORITY,
            'vulnerability_color_weight': cls.VULNERABILITY_COLOR_WEIGHT,
            'vulnerability_energy_weight': cls.VULNERABILITY_ENERGY_WEIGHT,
            'vulnerability_age_weight': cls.VULNERABILITY_AGE_WEIGHT,
            'deap_selection_method': cls.DEAP_SELECTION_METHOD,
            'deap_crossover_method': cls.DEAP_CROSSOVER_METHOD,
            'deap_population_size': cls.DEAP_POPULATION_SIZE,
            'deap_generations': cls.DEAP_GENERATIONS,
            'deap_hall_of_fame_size': cls.DEAP_HALL_OF_FAME_SIZE,

            # Parámetros de glucosa
            'initial_glucose_count': cls.INITIAL_GLUCOSE_COUNT,
            'max_glucose_count': cls.MAX_GLUCOSE_COUNT,
            'glucose_spawn_rate': cls.GLUCOSE_SPAWN_RATE,
            'glucose_min_size': cls.GLUCOSE_MIN_SIZE,
            'glucose_max_size': cls.GLUCOSE_MAX_SIZE,
            'glucose_energy_multiplier': cls.GLUCOSE_ENERGY_MULTIPLIER,
            'bacteria_glucose_consumption_rate': cls.BACTERIA_GLUCOSE_CONSUMPTION_RATE,
            'glucose_respawn_threshold': cls.GLUCOSE_RESPAWN_THRESHOLD,

            # Parámetros de reproducción
            'bacteria_reproduction_energy_threshold': cls.BACTERIA_REPRODUCTION_ENERGY_THRESHOLD,
            'bacteria_reproduction_energy_cost': cls.BACTERIA_REPRODUCTION_ENERGY_COST,
            'bacteria_reproduction_cooldown': cls.BACTERIA_REPRODUCTION_COOLDOWN,
            'bacteria_offset_distance': cls.BACTERIA_OFFSET_DISTANCE,
            'bacteria_reproduction_mutation_rate': cls.BACTERIA_REPRODUCTION_MUTATION_RATE,
        }
    
    @classmethod
    def validate_parameters(cls, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validar y normalizar parámetros"""
        validated = {}
        
        # Validar cada parámetro
        for key, value in parameters.items():
            if hasattr(cls, key.upper()):
                default = getattr(cls, key.upper())
                
                if isinstance(default, (int, float)):
                    # Validar rangos
                    if key in ['mutation_rate', 'crossover_rate']:
                        validated[key] = max(0.0, min(1.0, float(value)))
                    elif key in ['max_speed', 'turn_rate']:
                        validated[key] = max(0.0, float(value))
                    elif key in ['canvas_width', 'canvas_height']:
                        validated[key] = max(100, min(2000, int(value)))
                    else:
                        validated[key] = type(default)(value)
                elif isinstance(default, tuple):
                    # Convertir a tupla
                    if isinstance(value, list):
                        validated[key] = tuple(value)
                    elif isinstance(value, str):
                        # Convertir "r,g,b" a tupla
                        validated[key] = tuple(map(int, value.split(',')))
                    else:
                        validated[key] = tuple(value)
                else:
                    validated[key] = value
        
        return validated
    
    @classmethod
    def merge_with_defaults(cls, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Combinar parámetros dados con valores por defecto"""
        defaults = cls.get_default_parameters()
        validated = cls.validate_parameters(parameters)
        return {**defaults, **validated}
