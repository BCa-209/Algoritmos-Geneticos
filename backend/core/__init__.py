"""
Módulo core de la simulación de coevolución
"""
from .agents import Agent, Bacteria, Phagocyte, Glucose  # Añadir Glucose
from .simulation import Simulation
from .genetic_algorithm import GeneticAlgorithmDEAP as GeneticAlgorithm
from .fitness import (
    calculate_bacteria_fitness,
    calculate_phagocyte_fitness,
    calculate_coevolution_fitness
)

__all__ = [
    'Agent',
    'Bacteria', 
    'Phagocyte',
    'Glucose',  # Añadir Glucose
    'Simulation',
    'GeneticAlgorithm',
    'calculate_bacteria_fitness',
    'calculate_phagocyte_fitness',
    'calculate_coevolution_fitness'
]