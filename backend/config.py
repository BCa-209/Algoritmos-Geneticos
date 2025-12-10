"""
Configuración de la simulación
"""
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Dict, Any

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
            'phagocyte_center_ratio': cls.PHAGOCYTE_CENTER_RATIO
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