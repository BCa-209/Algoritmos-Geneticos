"""
Algoritmo genético para evolución de agentes
"""
import numpy as np
import random
from typing import List, Tuple, Dict, Any, Optional
from .agents import Agent, Bacteria, Phagocyte
from config import SimulationConfig

class GeneticAlgorithm:
    """Algoritmo genético para evolución de agentes"""
    
    def __init__(self, mutation_rate: float = None, 
                 crossover_rate: float = None,
                 mutation_strength: float = None):
        """Inicializar algoritmo genético"""
        self.mutation_rate = mutation_rate or SimulationConfig.MUTATION_RATE
        self.crossover_rate = crossover_rate or SimulationConfig.CROSSOVER_RATE
        self.mutation_strength = mutation_strength or SimulationConfig.MUTATION_STRENGTH
        
    def selection(self, agents: List[Agent], 
                  selection_type: str = 'tournament',
                  tournament_size: int = 3) -> List[Agent]:
        """Selección de padres basada en aptitud"""
        if not agents:
            return []
        
        selected_parents = []
        
        if selection_type == 'tournament':
            # Selección por torneo
            for _ in range(len(agents)):
                tournament = random.sample(agents, min(tournament_size, len(agents)))
                winner = max(tournament, key=lambda a: a.fitness)
                selected_parents.append(winner)
                
        elif selection_type == 'roulette':
            # Selección por ruleta (proporcional a fitness)
            total_fitness = sum(agent.fitness for agent in agents)
            if total_fitness > 0:
                probabilities = [agent.fitness / total_fitness for agent in agents]
                selected_parents = random.choices(agents, weights=probabilities, k=len(agents))
            else:
                selected_parents = random.choices(agents, k=len(agents))
                
        elif selection_type == 'rank':
            # Selección por ranking
            sorted_agents = sorted(agents, key=lambda a: a.fitness, reverse=True)
            ranks = list(range(1, len(sorted_agents) + 1))
            total_rank = sum(ranks)
            probabilities = [rank / total_rank for rank in ranks]
            selected_parents = random.choices(sorted_agents, weights=probabilities, k=len(agents))
        
        return selected_parents
    
    def crossover(self, parent1: Agent, parent2: Agent) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Cruce de genomas de dos padres"""
        genome1 = parent1.genome.copy()
        genome2 = parent2.genome.copy()
        
        child1_genome = {}
        child2_genome = {}
        
        # Cruzar cada gen del genoma
        for gene in genome1.keys():
            if random.random() < self.crossover_rate:
                # Intercambiar valores
                child1_genome[gene] = genome2.get(gene, genome1[gene])
                child2_genome[gene] = genome1.get(gene, genome2[gene])
            else:
                # Mantener valores originales
                child1_genome[gene] = genome1[gene]
                child2_genome[gene] = genome2[gene]
        
        return child1_genome, child2_genome
    
    def mutate(self, genome: Dict[str, float]) -> Dict[str, float]:
        """Aplicar mutación a un genoma"""
        mutated_genome = genome.copy()
        
        for gene, value in mutated_genome.items():
            if random.random() < self.mutation_rate:
                # Mutación gaussiana
                mutation = np.random.normal(0, self.mutation_strength)
                new_value = value + mutation
                
                # Asegurar que el valor esté en [0, 1]
                new_value = max(0.0, min(1.0, new_value))
                
                mutated_genome[gene] = new_value
        
        return mutated_genome
    
    def create_new_generation(self, agents: List[Agent], 
                             target_size: int,
                             elitism: int = 2) -> List[Agent]:
        """Crear nueva generación de agentes"""
        if not agents:
            return []
        
        # Ordenar por fitness
        agents.sort(key=lambda a: a.fitness, reverse=True)
        new_generation = []
        
        # Elitismo: mantener los mejores agentes
        for i in range(min(elitism, len(agents))):
            elite = agents[i].copy()
            elite.id = f"{elite.species}_{len(new_generation)}"
            new_generation.append(elite)
        
        # Selección de padres
        parents = self.selection(agents, selection_type='tournament')
        
        # Reproducción hasta alcanzar tamaño objetivo
        while len(new_generation) < target_size:
            # Seleccionar dos padres aleatorios
            if len(parents) < 2:
                break
                
            parent1, parent2 = random.sample(parents, 2)
            
            # Cruzar
            child1_genome, child2_genome = self.crossover(parent1, parent2)
            
            # Mutar
            child1_genome = self.mutate(child1_genome)
            child2_genome = self.mutate(child2_genome)
            
            # Crear nuevos agentes - IMPORTANTE: verificar el tipo correcto
            if parent1.species == 'bacteria':
                child1 = Bacteria(genome=child1_genome)
                child2 = Bacteria(genome=child2_genome)
            else:
                child1 = Phagocyte(genome=child1_genome)
                child2 = Phagocyte(genome=child2_genome)
            
            # Asignar IDs únicos
            child1.id = f"{child1.species}_{len(new_generation)}"
            new_generation.append(child1)
            
            if len(new_generation) < target_size:
                child2.id = f"{child2.species}_{len(new_generation)}"
                new_generation.append(child2)
        
        return new_generation
    
    def evolve_population(self, bacteria: List[Bacteria], 
                         phagocytes: List[Phagocyte],
                         background_color: Tuple[int, int, int]) -> Tuple[List[Bacteria], List[Phagocyte]]:
        """Evolucionar ambas poblaciones de forma coevolutiva"""
        
        # Calcular fitness para bacterias (basado en camuflaje)
        for bacteria_agent in bacteria:
            bacteria_agent.calculate_fitness(background_color)
        
        # Calcular fitness para fagocitos (basado en éxito de caza)
        for phagocyte in phagocytes:
            phagocyte.calculate_fitness(background_color, bacteria)
        
        # Crear nueva generación para cada especie
        new_bacteria = self.create_new_generation(
            bacteria, 
            target_size=len(bacteria)
        )
        
        new_phagocytes = self.create_new_generation(
            phagocytes,
            target_size=len(phagocytes)
        )
        
        return new_bacteria, new_phagocytes
    
    def update_parameters(self, mutation_rate: float = None,
                         crossover_rate: float = None,
                         mutation_strength: float = None):
        """Actualizar parámetros del algoritmo genético"""
        if mutation_rate is not None:
            self.mutation_rate = max(0.0, min(1.0, mutation_rate))
        if crossover_rate is not None:
            self.crossover_rate = max(0.0, min(1.0, crossover_rate))
        if mutation_strength is not None:
            self.mutation_strength = max(0.0, mutation_strength)