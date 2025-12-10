"""
Representación del genoma de un agente
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
import random
import numpy as np

@dataclass
class Genome:
    """Representación del genoma de un agente"""
    
    genes: Dict[str, float] = field(default_factory=dict)
    species: str = "unknown"
    
    def __post_init__(self):
        """Inicializar genoma por defecto según especie"""
        if not self.genes:
            if self.species == "bacteria":
                self.genes = {
                    'color_gene': random.random(),
                    'length_gene': random.random(),  # Nueva: gen de longitud
                    'width_gene': random.random(),   # Nueva: gen de grosor
                    'reproduction_rate': random.random(),
                    'metabolism': random.random()
                }
            elif self.species == "phagocyte":
                self.genes = {
                    'sensitivity_gene': random.random(),
                    'speed_gene': random.random(),
                    'vision_gene': random.random(),
                    'aggression_gene': random.random(),  # Nuevo gen
                    'endurance_gene': random.random()
                }
    
    @classmethod
    def create_random(cls, species: str) -> 'Genome':
        """Crear genoma aleatorio para especie dada"""
        genome = cls(species=species)
        return genome
    
    @classmethod
    def crossover(cls, parent1: 'Genome', parent2: 'Genome') -> Tuple['Genome', 'Genome']:
        """Cruce de dos genomas padres"""
        if parent1.species != parent2.species:
            raise ValueError("Los genomas deben ser de la misma especie")
        
        child1_genes = {}
        child2_genes = {}
        
        for gene_name in parent1.genes.keys():
            if gene_name in parent2.genes:
                # Intercambiar genes con probabilidad 50%
                if random.random() < 0.5:
                    child1_genes[gene_name] = parent2.genes[gene_name]
                    child2_genes[gene_name] = parent1.genes[gene_name]
                else:
                    child1_genes[gene_name] = parent1.genes[gene_name]
                    child2_genes[gene_name] = parent2.genes[gene_name]
            else:
                child1_genes[gene_name] = parent1.genes[gene_name]
        
        # Agregar genes únicos del padre 2
        for gene_name in parent2.genes.keys():
            if gene_name not in child1_genes:
                child1_genes[gene_name] = parent2.genes[gene_name]
            if gene_name not in child2_genes:
                child2_genes[gene_name] = parent2.genes[gene_name]
        
        return (
            cls(genes=child1_genes, species=parent1.species),
            cls(genes=child2_genes, species=parent1.species)
        )
    
    def mutate(self, mutation_rate: float = 0.01, 
               mutation_strength: float = 0.1) -> 'Genome':
        """Aplicar mutación al genoma"""
        mutated_genes = self.genes.copy()
        
        for gene_name, value in mutated_genes.items():
            if random.random() < mutation_rate:
                # Mutación gaussiana
                mutation = np.random.normal(0, mutation_strength)
                new_value = value + mutation
                
                # Asegurar que el valor esté en [0, 1]
                new_value = max(0.0, min(1.0, new_value))
                
                mutated_genes[gene_name] = new_value
        
        return Genome(genes=mutated_genes, species=self.species)
    
    def get_gene(self, gene_name: str, default: float = 0.5) -> float:
        """Obtener valor de un gen"""
        return self.genes.get(gene_name, default)
    
    def set_gene(self, gene_name: str, value: float):
        """Establecer valor de un gen"""
        self.genes[gene_name] = max(0.0, min(1.0, value))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir genoma a diccionario"""
        return {
            'species': self.species,
            'genes': self.genes,
            'gene_count': len(self.genes)
        }
    
    def copy(self) -> 'Genome':
        return Genome(genes=self.genes.copy(), species=self.species)
        """Crear copia del genoma"""