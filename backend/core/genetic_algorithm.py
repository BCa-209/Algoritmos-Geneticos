"""
Algoritmo genético simplificado que funciona con DEAP
"""
import random
import numpy as np
from typing import List, Tuple, Dict, Any
from deap import base, creator, tools, algorithms

from .agents import Bacteria, Phagocyte
from models.genome import Genome
from config import SimulationConfig

# Crear tipos DEAP una sola vez
try:
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("BacteriaIndividual", dict, fitness=creator.FitnessMax)
    creator.create("PhagocyteIndividual", dict, fitness=creator.FitnessMax)
except Exception:
    pass  # Los tipos ya existen

class GeneticAlgorithmDEAP:
    """Algoritmo genético que usa DEAP - Versión corregida"""
    
    def __init__(self, 
                mutation_rate: float = None,
                crossover_rate: float = None,
                mutation_strength: float = None):
        
        self.mutation_rate = mutation_rate or SimulationConfig.MUTATION_RATE
        self.crossover_rate = crossover_rate or SimulationConfig.CROSSOVER_RATE
        self.mutation_strength = mutation_strength or SimulationConfig.MUTATION_STRENGTH
        
        # Crear toolboxes
        self.bacteria_toolbox = self._create_bacteria_toolbox()
        self.phagocyte_toolbox = self._create_phagocyte_toolbox()
    
    def _create_bacteria_toolbox(self):
        """Crear toolbox para bacterias"""
        toolbox = base.Toolbox()
        
        # Función para crear individuo bacteria
        def create_bacteria_individual():
            genome = Genome.create_random("bacteria")
            ind = creator.BacteriaIndividual(genome.genes)
            return ind
        
        toolbox.register("individual", create_bacteria_individual)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        
        # Operadores genéticos
        toolbox.register("mate", self._cx_uniform, indpb=0.5)
        toolbox.register("mutate", self._mutate_gaussian, 
                        mu=0, sigma=self.mutation_strength, indpb=self.mutation_rate)
        toolbox.register("select", tools.selTournament, tournsize=3)
        
        return toolbox
    
    def _create_phagocyte_toolbox(self):
        """Crear toolbox para fagocitos"""
        toolbox = base.Toolbox()
        
        # Función para crear individuo fagocito
        def create_phagocyte_individual():
            genome = Genome.create_random("phagocyte")
            ind = creator.PhagocyteIndividual(genome.genes)
            return ind
        
        toolbox.register("individual", create_phagocyte_individual)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        
        # Operadores genéticos
        toolbox.register("mate", self._cx_uniform, indpb=0.5)
        toolbox.register("mutate", self._mutate_gaussian, 
                        mu=0, sigma=self.mutation_strength * 1.5, indpb=self.mutation_rate * 1.2)
        toolbox.register("select", tools.selTournament, tournsize=5)
        
        return toolbox
    
    def _cx_uniform(self, ind1, ind2, indpb):
        """Cruce uniforme"""
        for key in ind1:
            if random.random() < indpb:
                ind1[key], ind2[key] = ind2[key], ind1[key]
        return ind1, ind2
    
    def _mutate_gaussian(self, individual, mu, sigma, indpb):
        """Mutación gaussiana"""
        for key in individual:
            if random.random() < indpb:
                individual[key] += random.gauss(mu, sigma)
                individual[key] = max(0.0, min(1.0, individual[key]))
        return individual,
    
    def evaluate_bacteria_fitness(self, individual, background_color):
        """Evaluar fitness de bacteria"""
        bacteria = Bacteria(genome=dict(individual))
        bacteria.calculate_fitness(background_color)
        return (bacteria.fitness,)
    
    def evaluate_phagocyte_fitness(self, individual, background_color, bacteria_list):
        """Evaluar fitness de fagocito"""
        phagocyte = Phagocyte(genome=dict(individual))
        phagocyte.calculate_fitness(background_color, bacteria_list)
        return (phagocyte.fitness,)
    
    def evolve_population(self, bacteria: List[Bacteria], 
                         phagocytes: List[Phagocyte],
                         background_color: Tuple[int, int, int]) -> Tuple[List[Bacteria], List[Phagocyte]]:
        """Evolucionar ambas poblaciones usando DEAP"""
        
        # 1. Convertir bacterias a población DEAP
        bacteria_population = []
        for bact in bacteria:
            if isinstance(bact, Bacteria):
                ind = creator.BacteriaIndividual(bact.genome)
                ind.fitness.values = (bact.fitness,)
                bacteria_population.append(ind)
        
        # 2. Convertir fagocitos a población DEAP
        phagocyte_population = []
        for phago in phagocytes:
            if isinstance(phago, Phagocyte):
                ind = creator.PhagocyteIndividual(phago.genome)
                ind.fitness.values = (phago.fitness,)
                phagocyte_population.append(ind)
        
        # 3. Asegurar tamaño mínimo de población
        min_pop_size = 5
        if len(bacteria_population) < min_pop_size:
            extra = self.bacteria_toolbox.population(n=min_pop_size - len(bacteria_population))
            bacteria_population.extend(extra)
        
        if len(phagocyte_population) < min_pop_size:
            extra = self.phagocyte_toolbox.population(n=min_pop_size - len(phagocyte_population))
            phagocyte_population.extend(extra)
        
        # 4. Configurar evaluación
        self.bacteria_toolbox.register("evaluate", 
                                     self.evaluate_bacteria_fitness,
                                     background_color=background_color)
        
        self.phagocyte_toolbox.register("evaluate",
                                      self.evaluate_phagocyte_fitness,
                                      background_color=background_color,
                                      bacteria_list=bacteria)
        
        # 5. Evolucionar bacterias
        if bacteria_population:
            # Evaluar población inicial
            for ind in bacteria_population:
                if not ind.fitness.valid:
                    ind.fitness.values = self.bacteria_toolbox.evaluate(ind)
            
            # Ejecutar una generación
            bacteria_population = self._run_one_generation(
                bacteria_population, self.bacteria_toolbox,
                self.crossover_rate, self.mutation_rate
            )
        
        # 6. Evolucionar fagocitos
        if phagocyte_population:
            # Evaluar población inicial
            for ind in phagocyte_population:
                if not ind.fitness.valid:
                    ind.fitness.values = self.phagocyte_toolbox.evaluate(ind)
            
            # Ejecutar una generación
            phagocyte_population = self._run_one_generation(
                phagocyte_population, self.phagocyte_toolbox,
                self.crossover_rate * 0.8, self.mutation_rate * 1.2
            )
        
        # 7. Convertir de vuelta a agentes
        new_bacteria = []
        for ind in bacteria_population:
            if hasattr(ind, 'genes'):
                genome_dict = ind.genes
            else:
                genome_dict = dict(ind)
            
            new_bact = Bacteria(genome=genome_dict)
            new_bacteria.append(new_bact)
        
        new_phagocytes = []
        for ind in phagocyte_population:
            if hasattr(ind, 'genes'):
                genome_dict = ind.genes
            else:
                genome_dict = dict(ind)
            
            new_phago = Phagocyte(genome=genome_dict)
            new_phagocytes.append(new_phago)
        
        return new_bacteria, new_phagocytes
    
    def _run_one_generation(self, population, toolbox, cxpb, mutpb):
        """Ejecutar una generación de evolución"""
        # 1. Seleccionar padres
        offspring = toolbox.select(population, len(population))
        
        # 2. Clonar los seleccionados
        offspring = list(map(toolbox.clone, offspring))
        
        # 3. Aplicar cruce y mutación
        for i in range(1, len(offspring), 2):
            if random.random() < cxpb:
                offspring[i-1], offspring[i] = toolbox.mate(offspring[i-1], offspring[i])
                del offspring[i-1].fitness.values
                del offspring[i].fitness.values
        
        for i in range(len(offspring)):
            if random.random() < mutpb:
                offspring[i], = toolbox.mutate(offspring[i])
                del offspring[i].fitness.values
        
        # 4. Evaluar hijos con fitness inválido
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # 5. Reemplazar población
        population[:] = offspring
        
        return population
    
    def update_parameters(self, mutation_rate: float = None,
                        crossover_rate: float = None,
                        mutation_strength: float = None):
        """Actualizar parámetros del algoritmo"""
        if mutation_rate is not None:
            self.mutation_rate = max(0.0, min(1.0, mutation_rate))
        if crossover_rate is not None:
            self.crossover_rate = max(0.0, min(1.0, crossover_rate))
        if mutation_strength is not None:
            self.mutation_strength = max(0.0, mutation_strength)