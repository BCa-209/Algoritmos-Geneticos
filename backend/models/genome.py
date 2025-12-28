"""
Representación simplificada del genoma compatible con DEAP
"""
import random
import numpy as np
from typing import Dict, List, Tuple, Any

class Genome:
    """Representación del genoma de un agente - VERSIÓN SIMPLIFICADA"""
    
    def __init__(self, genes: Dict[str, float] = None, species: str = "unknown"):
        self.genes = genes or {}
        self.species = species
        
        # Inicializar genoma por defecto según especie
        if not self.genes:
            self._initialize_default_genome()
    
    def _initialize_default_genome(self):
        """Inicializar genoma por defecto según especie"""
        if self.species == "bacteria":
            self.genes = {
                'color_gene': random.random(),
                'length_gene': random.random(),
                'width_gene': random.random(),
                'reproduction_rate': random.random(),
                'metabolism': random.random()
            }
        elif self.species == "phagocyte":
            self.genes = {
                'sensitivity_gene': random.random(),
                'speed_gene': random.random(),
                'vision_gene': random.random(),
                'aggression_gene': random.random(),
                'endurance_gene': random.random()
            }
    
    @classmethod
    def create_random(cls, species: str) -> 'Genome':
        """Crear genoma aleatorio para especie dada"""
        return cls(species=species)
    
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
        """Crear copia del genoma"""
        return Genome(genes=self.genes.copy(), species=self.species)