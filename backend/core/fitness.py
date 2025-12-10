"""
Funciones de fitness para la simulación coevolutiva
"""
import numpy as np
import math
from typing import List, Tuple, Dict, Any
from .agents import Bacteria, Phagocyte

def calculate_color_distance(color1: Tuple[int, int, int], 
                        color2: Tuple[int, int, int]) -> float:
    """Calcular distancia normalizada entre dos colores RGB"""
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    
    # Distancia euclidiana normalizada a [0,1]
    distance = math.sqrt(
        ((r1 - r2) / 255) ** 2 +
        ((g1 - g2) / 255) ** 2 +
        ((b1 - b2) / 255) ** 2
    ) / math.sqrt(3)
    
    return distance

def calculate_bacteria_fitness(bacteria: Bacteria, 
                             background_color: Tuple[int, int, int]) -> float:
    """Calcular fitness de bacteria basado en camuflaje"""
    color_diff = calculate_color_distance(bacteria.color, background_color)
    
    # Fitness es inversamente proporcional a la diferencia de color
    fitness = max(0.0, 1.0 - color_diff)
    
    # Añadir bonus por energía
    energy_bonus = bacteria.energy / 200.0
    fitness = 0.7 * fitness + 0.3 * energy_bonus
    
    return fitness

def calculate_phagocyte_fitness(phagocyte: Phagocyte,
                              background_color: Tuple[int, int, int],
                              bacteria_list: List[Bacteria]) -> float:
    """Calcular fitness de fagocito basado en éxito de detección"""
    sensitivity = phagocyte.genome.get('sensitivity_gene', 0.5)
    
    # Fitness base basado en sensibilidad
    fitness = sensitivity
    
    # Bonus por energía
    energy_bonus = phagocyte.energy / 200.0
    fitness = 0.6 * fitness + 0.4 * energy_bonus
    
    # Si hay bacterias, ajustar fitness basado en éxito potencial de detección
    if bacteria_list and len(bacteria_list) > 0:
        # Calcular cuántas bacterias serían detectables
        detectable_count = 0
        for bacteria in bacteria_list:
            if phagocyte.detect_bacteria(bacteria, background_color):
                detectable_count += 1
        
        detection_rate = detectable_count / len(bacteria_list)
        fitness = 0.5 * fitness + 0.5 * detection_rate
    
    return fitness

def calculate_coevolution_fitness(bacteria_list: List[Bacteria],
                                phagocyte_list: List[Phagocyte],
                                background_color: Tuple[int, int, int]) -> Dict[str, Any]:
    """Calcular fitness coevolutivo para ambas poblaciones"""
    # Calcular fitness individual
    bacteria_fitness = []
    for bacteria in bacteria_list:
        fitness = calculate_bacteria_fitness(bacteria, background_color)
        bacteria.fitness = fitness
        bacteria_fitness.append(fitness)
    
    phagocyte_fitness = []
    for phagocyte in phagocyte_list:
        fitness = calculate_phagocyte_fitness(phagocyte, background_color, bacteria_list)
        phagocyte.fitness = fitness
        phagocyte_fitness.append(fitness)
    
    # Estadísticas coevolutivas
    if bacteria_fitness and phagocyte_fitness:
        # Coevolución: el éxito de uno depende del fracaso del otro
        avg_bacteria_fitness = np.mean(bacteria_fitness)
        avg_phagocyte_fitness = np.mean(phagocyte_fitness)
        
        # Ajustar fitness basado en interacción
        coevolution_factor = 1.0 - abs(avg_bacteria_fitness - avg_phagocyte_fitness)
        
        for bacteria in bacteria_list:
            bacteria.fitness *= coevolution_factor
        
        for phagocyte in phagocyte_list:
            phagocyte.fitness *= coevolution_factor
    
    return {
        'bacteria': {
            'average': np.mean(bacteria_fitness) if bacteria_fitness else 0.0,
            'max': max(bacteria_fitness) if bacteria_fitness else 0.0,
            'min': min(bacteria_fitness) if bacteria_fitness else 0.0
        },
        'phagocytes': {
            'average': np.mean(phagocyte_fitness) if phagocyte_fitness else 0.0,
            'max': max(phagocyte_fitness) if phagocyte_fitness else 0.0,
            'min': min(phagocyte_fitness) if phagocyte_fitness else 0.0
        }
    }