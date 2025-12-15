"""
Agentes de la simulación: Bacterias y Fagocitos
"""
import numpy as np
import random
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from config import SimulationConfig

@dataclass
class Agent:
    """Clase base para todos los agentes"""
    
    id: str
    species: str
    x: float
    y: float
    genome: Dict[str, float]
    color: Tuple[int, int, int]
    fitness: float = 0.0
    energy: float = 100.0
    age: int = 0
    
    def __post_init__(self):
        """Inicialización después de la creación"""
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.normalize_velocity()
    
    def normalize_velocity(self):
        """Normalizar vector de velocidad"""
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > 0:
            self.vx /= speed
            self.vy /= speed
    
    def move(self, canvas_width: int, canvas_height: int):
        """Mover agente con rebote realista en los bordes"""
        max_speed = SimulationConfig.MAX_SPEED
        
        # Añadir aleatoriedad al movimiento
        turn_rate = SimulationConfig.TURN_RATE
        self.vx += random.uniform(-turn_rate, turn_rate)
        self.vy += random.uniform(-turn_rate, turn_rate)
        self.normalize_velocity()
        
        # Calcular nueva posición
        new_x = self.x + self.vx * max_speed
        new_y = self.y + self.vy * max_speed
        
        # Tamaño del agente para colisiones
        if self.species == 'bacteria':
            agent_size = SimulationConfig.AGENT_SIZE
        else:
            agent_size = SimulationConfig.PHAGOCYTE_SIZE
        
        # Verificar colisión con bordes
        collided_with_border = False
        
        # Colisión con borde izquierdo
        if new_x - agent_size < 0:
            self.vx = abs(self.vx)  # Rebotar hacia la derecha
            new_x = agent_size
            collided_with_border = True
        
        # Colisión con borde derecho
        elif new_x + agent_size > canvas_width:
            self.vx = -abs(self.vx)  # Rebotar hacia la izquierda
            new_x = canvas_width - agent_size
            collided_with_border = True
        
        # Colisión con borde superior
        if new_y - agent_size < 0:
            self.vy = abs(self.vy)  # Rebotar hacia abajo
            new_y = agent_size
            collided_with_border = True
        
        # Colisión con borde inferior
        elif new_y + agent_size > canvas_height:
            self.vy = -abs(self.vy)  # Rebotar hacia arriba
            new_y = canvas_height - agent_size
            collided_with_border = True
        
        # Aplicar nueva posición
        self.x = new_x
        self.y = new_y
        
        # Si hubo colisión, añadir un pequeño efecto de "rebote"
        if collided_with_border:
            # Reducir velocidad temporalmente por la colisión
            self.vx *= 0.9
            self.vy *= 0.9
            self.normalize_velocity()
        
        # Envejecer y perder energía
        self.age += 1
        self.energy -= SimulationConfig.ENERGY_LOSS
        
        # Normalizar energía
        self.energy = max(0.0, min(200.0, self.energy))
    
    def is_alive(self) -> bool:
        """Verificar si el agente está vivo"""
        return self.energy > 0 and self.age < 1000
    
    def copy(self) -> 'Agent':
        """Crear una copia del agente"""
        return Agent(
            id=self.id,
            species=self.species,
            x=self.x,
            y=self.y,
            genome=self.genome.copy(),
            color=self.color,
            fitness=self.fitness,
            energy=self.energy,
            age=self.age
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir agente a diccionario para serialización"""
        return {
            'id': self.id,
            'species': self.species,
            'x': self.x,
            'y': self.y,
            'color': self.color,
            'fitness': self.fitness,
            'energy': self.energy,
            'age': self.age,
            'genome': self.genome,
            'vx': getattr(self, 'vx', 0),
            'vy': getattr(self, 'vy', 0)
        }
    
    def detect_bacteria(self, bacteria: 'Bacteria', background_color: Tuple[int, int, int]) -> bool:
        """Método por defecto para detectar bacterias (debe ser sobrescrito por Phagocyte)"""
        raise NotImplementedError("Este método debe ser implementado por subclases")
    
    def get_vulnerability_score(self, background_color: Tuple[int, int, int]) -> float:
        """Método por defecto para obtener puntaje de vulnerabilidad (debe ser sobrescrito por Bacteria)"""
        raise NotImplementedError("Este método debe ser implementado por subclases")


class Bacteria(Agent):
    """Agente Bacteria (presa) - Forma de bastón (bacilo)"""
    
    def __init__(self, id: str = None, 
                 x: float = None, 
                 y: float = None,
                 genome: Dict[str, float] = None):
        """Inicializar bacteria"""
        # Valores por defecto
        if genome is None:
            genome = {
                'color_gene': random.random(),
                'length_gene': random.random(),  # Nueva: gen de longitud
                'width_gene': random.random()    # Nueva: gen de grosor
            }
        
        # Generar color basado en gen de color
        color_gene = genome.get('color_gene', random.random())
        color = self.genome_to_color(color_gene)
        
        # Dimensiones del bastón basadas en genes
        self.length_gene = genome.get('length_gene', random.random())
        self.width_gene = genome.get('width_gene', random.random())
        
        # Posición aleatoria si no se especifica
        if x is None:
            x = random.uniform(0, SimulationConfig.CANVAS_WIDTH)
        if y is None:
            y = random.uniform(0, SimulationConfig.CANVAS_HEIGHT)
        
        if id is None:
            id = f"bacteria_{random.randint(1000, 9999)}"
        
        super().__init__(
            id=id,
            species='bacteria',
            x=x,
            y=y,
            genome=genome,
            color=color
        )
        
        # Dirección inicial aleatoria
        self.direction = random.uniform(0, 2 * math.pi)
    
    def genome_to_color(self, color_gene: float) -> Tuple[int, int, int]:
        """Convertir gen de color a RGB para bacterias"""
        # Colores más naturales para bacterias
        r = int(150 + 100 * math.sin(color_gene * math.pi))
        g = int(150 + 100 * math.sin(color_gene * math.pi * 1.7))
        b = int(150 + 100 * math.sin(color_gene * math.pi * 2.3))
        
        return (r, g, b)
    
    def move(self, canvas_width: int, canvas_height: int):
        """Mover bacteria con forma de bastón"""
        # Primero llamar al movimiento base
        super().move(canvas_width, canvas_height)
        
        # Actualizar dirección basada en velocidad
        if abs(self.vx) > 0.01 or abs(self.vy) > 0.01:
            self.direction = math.atan2(self.vy, self.vx)
    
    def calculate_fitness(self, background_color: Tuple[int, int, int]):
        """Calcular fitness basado en camuflaje"""
        # Fitness = 1 - diferencia_de_color
        bg_r, bg_g, bg_b = background_color
        r, g, b = self.color
        
        # Calcular distancia euclidiana en espacio RGB normalizado
        color_diff = math.sqrt(
            ((r - bg_r) / 255) ** 2 +
            ((g - bg_g) / 255) ** 2 +
            ((b - bg_b) / 255) ** 2
        ) / math.sqrt(3)  # Normalizar a [0,1]
        
        # Fitness inverso a la diferencia de color
        self.fitness = max(0.0, 1.0 - color_diff)
        
        # Añadir bonus por energía
        energy_bonus = self.energy / 200.0
        self.fitness = 0.7 * self.fitness + 0.3 * energy_bonus
    
    def calculate_vulnerability(self, background_color: Tuple[int, int, int]) -> float:
        """Calcular vulnerabilidad basada en diferencia de color (inverso del fitness de camuflaje)"""
        # Calcular diferencia de color con fondo
        bg_r, bg_g, bg_b = background_color
        r, g, b = self.color
        
        color_diff = math.sqrt(
            ((r - bg_r) / 255) ** 2 +
            ((g - bg_g) / 255) ** 2 +
            ((b - bg_b) / 255) ** 2
        ) / math.sqrt(3)
        
        # Vulnerabilidad = diferencia de color (1.0 = muy visible, 0.0 = invisible)
        return color_diff
    
    def get_vulnerability_score(self, background_color: Tuple[int, int, int]) -> float:
        """Obtener puntaje de vulnerabilidad completo (incluye energía y edad)"""
        color_vulnerability = self.calculate_vulnerability(background_color)
        
        # Usar parámetros configurables
        color_weight = SimulationConfig.VULNERABILITY_COLOR_WEIGHT
        energy_weight = SimulationConfig.VULNERABILITY_ENERGY_WEIGHT
        age_weight = SimulationConfig.VULNERABILITY_AGE_WEIGHT
        
        # Ajustar por energía: bacterias con baja energía son más lentas/fáciles de cazar
        energy_factor = 1.0 - (self.energy / 200.0)  # 1.0 cuando energía baja
        
        # Ajustar por edad: bacterias viejas pueden ser más lentas
        age_factor = min(1.0, self.age / 500.0)  # Más vulnerable cuando es vieja
        
        # Puntaje compuesto de vulnerabilidad usando pesos configurables
        vulnerability_score = (
            color_weight * color_vulnerability +  # Peso configurable para color
            energy_weight * energy_factor +       # Peso configurable para energía
            age_weight * age_factor              # Peso configurable para edad
        )
        
        return min(1.0, max(0.0, vulnerability_score))
    
    def reproduce(self) -> Optional['Bacteria']:
        """Reproducción asexual (si tiene suficiente energía)"""
        if self.energy > 150:
            self.energy -= 50
            
            # Crear nueva bacteria con mutación
            child_genome = self.genome.copy()
            
            # Mutación en genes de color
            if random.random() < SimulationConfig.MUTATION_RATE:
                color_gene = child_genome.get('color_gene', random.random())
                color_gene += random.uniform(-0.1, 0.1)
                color_gene = max(0.0, min(1.0, color_gene))
                child_genome['color_gene'] = color_gene
            
            # Mutación en genes de forma
            if random.random() < SimulationConfig.MUTATION_RATE:
                length_gene = child_genome.get('length_gene', random.random())
                length_gene += random.uniform(-0.1, 0.1)
                length_gene = max(0.0, min(1.0, length_gene))
                child_genome['length_gene'] = length_gene
            
            if random.random() < SimulationConfig.MUTATION_RATE:
                width_gene = child_genome.get('width_gene', random.random())
                width_gene += random.uniform(-0.1, 0.1)
                width_gene = max(0.0, min(1.0, width_gene))
                child_genome['width_gene'] = width_gene
            
            child = Bacteria(genome=child_genome)
            child.x = self.x + random.uniform(-20, 20)
            child.y = self.y + random.uniform(-20, 20)
            child.direction = self.direction + random.uniform(-0.5, 0.5)
            
            return child
        
        return None
    
    def get_bacillus_dimensions(self):
        """Obtener dimensiones del bastón"""
        # Longitud base del bastón
        base_length = SimulationConfig.BACILLUS_BASE_LENGTH
        length = base_length * (0.8 + 0.4 * self.length_gene)
        
        # Grosor base del bastón
        base_width = SimulationConfig.BACILLUS_BASE_WIDTH
        width = base_width * (0.7 + 0.6 * self.width_gene)
        
        return length, width
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir bacteria a diccionario incluyendo propiedades específicas"""
        data = super().to_dict()
        data.update({
            'direction': self.direction,
            'length_gene': self.length_gene,
            'width_gene': self.width_gene
        })
        return data


class Phagocyte(Agent):
    """Agente Fagocito (cazador) - Forma circular con centro negro"""
    
    def __init__(self, id: str = None,
                 x: float = None,
                 y: float = None,
                 genome: Dict[str, float] = None,
                 spawn_point: Tuple[float, float] = None):
        """Inicializar fagocito con punto de aparición"""
        
        # Determinar posición de aparición
        if x is None or y is None:
            spawn_mode = SimulationConfig.PHAGOCYTE_SPAWN_MODE
            
            if spawn_mode == 'fixed_point':
                # Usar punto de spawn personalizado o el predeterminado
                if spawn_point is not None:
                    center_x, center_y = spawn_point
                else:
                    center_x = SimulationConfig.PHAGOCYTE_SPAWN_POINT[0]
                    center_y = SimulationConfig.PHAGOCYTE_SPAWN_POINT[1]
                
                radius = SimulationConfig.PHAGOCYTE_SPAWN_RADIUS
                
                # Crear posición aleatoria dentro del radio
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, radius)
                
                x = center_x + distance * math.cos(angle)
                y = center_y + distance * math.sin(angle)
                
                # Dirección inicial aleatoria lejos del centro
                direction_away = angle + random.uniform(-0.5, 0.5)
                self.vx = math.cos(direction_away)
                self.vy = math.sin(direction_away)
                self.normalize_velocity()
                
                print(f"Fagocito creado en posición fija: ({x:.1f}, {y:.1f})")
            else:
                # Modo aleatorio tradicional
                x = random.uniform(0, SimulationConfig.CANVAS_WIDTH)
                y = random.uniform(0, SimulationConfig.CANVAS_HEIGHT)
        
        # Valores por defecto del genoma
        if genome is None:
            genome = {
                'sensitivity_gene': random.random(),
                'speed_gene': random.random(),
                'vision_gene': random.random(),
                'aggression_gene': random.random()
            }
        
        # Color basado en genes de agresividad y sensibilidad
        sensitivity = genome.get('sensitivity_gene', random.random())
        aggression = genome.get('aggression_gene', random.random())
        
        # Color azulado-rojizo para fagocitos (más rojo = más agresivo)
        color = (
            int(100 + 155 * aggression),      # Rojo basado en agresividad
            int(100 + 100 * sensitivity),     # Verde basado en sensibilidad
            int(200 - 100 * aggression)       # Azul inverso a agresividad
        )
        
        if id is None:
            id = f"phagocyte_{random.randint(1000, 9999)}"
        
        # Inicializar clase base
        super().__init__(
            id=id,
            species='phagocyte',
            x=x,
            y=y,
            genome=genome,
            color=color
        )
        
        # Asegurar que la velocidad esté inicializada si no se estableció arriba
        if not hasattr(self, 'vx') or not hasattr(self, 'vy'):
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(-1, 1)
            self.normalize_velocity()
    
    def calculate_fitness(self, background_color: Tuple[int, int, int],
                         bacteria_list: List[Bacteria] = None):
        """Calcular fitness basado en éxito de caza"""
        # El fitness del fagocito depende de su sensibilidad
        sensitivity = self.genome.get('sensitivity_gene', 0.5)
        aggression = self.genome.get('aggression_gene', 0.5)
        
        # Fitness base basado en sensibilidad y agresividad
        self.fitness = 0.6 * sensitivity + 0.4 * aggression
        
        # Bonus por energía
        energy_bonus = self.energy / 200.0
        self.fitness = 0.6 * self.fitness + 0.4 * energy_bonus
        
        # Si hay bacterias, ajustar fitness basado en éxito histórico
        if bacteria_list and len(bacteria_list) > 0:
            avg_bacteria_fitness = sum(b.fitness for b in bacteria_list) / len(bacteria_list)
            # Fagocitos más sensibles y agresivos detectan mejor
            detection_success = max(0.0, 1.0 - avg_bacteria_fitness * (1 - sensitivity * aggression))
            self.fitness = 0.5 * self.fitness + 0.5 * detection_success
    
    def detect_bacteria(self, bacteria: Bacteria, background_color: Tuple[int, int, int]) -> bool:
        """Detectar bacteria basado en sensibilidad y diferencia de color"""
        sensitivity = self.genome.get('sensitivity_gene', 0.5)
        aggression = self.genome.get('aggression_gene', 0.5)
        
        # Calcular diferencia de color entre bacteria y fondo
        bg_r, bg_g, bg_b = background_color
        bact_r, bact_g, bact_b = bacteria.color
        
        color_diff = math.sqrt(
            ((bact_r - bg_r) / 255) ** 2 +
            ((bact_g - bg_g) / 255) ** 2 +
            ((bact_b - bg_b) / 255) ** 2
        ) / math.sqrt(3)
        
        # Obtener fitness de camuflaje de la bacteria
        bacteria_fitness = bacteria.fitness  # Este ya incluye el cálculo de camuflaje
        
        # El fagocito detecta si la diferencia de color > umbral ajustado por camuflaje
        # Las bacterias con alto fitness de camuflaje son más difíciles de detectar
        camouflage_effect = 1.0 - bacteria_fitness  # Inverso del fitness
        
        # Umbral de detección: fagocitos más sensibles y agresivos tienen mejor detección
        base_threshold = 1.0 - (sensitivity * (0.7 + 0.3 * aggression))
        
        # Ajustar umbral con el efecto de camuflaje de la bacteria
        # Cuando bacteria_fitness es alto (buen camuflaje), el umbral aumenta (más difícil detectar)
        adjusted_threshold = base_threshold * (0.5 + 0.5 * camouflage_effect)
        
        return color_diff > adjusted_threshold
    
    def find_target_bacteria(self, simulation) -> Optional[Bacteria]:
        """Buscar bacteria objetivo usando sistema de ranking"""
        # Obtener bacterias rankeadas dentro del rango
        ranked_bacteria = simulation.get_ranked_bacteria_in_range(self)
        
        if not ranked_bacteria:
            return None
        
        # La primera bacteria en la lista es la más vulnerable dentro del rango
        return ranked_bacteria[0]
    
    def move(self, canvas_width: int, canvas_height: int, simulation=None):
        """Mover fagocito con búsqueda inteligente"""
        if simulation and hasattr(self, 'find_target_bacteria'):
            # Buscar bacteria objetivo usando ranking
            target_bacteria = self.find_target_bacteria(simulation)
            
            if target_bacteria:
                # Perseguir la bacteria objetivo
                self.chase_bacteria(target_bacteria)
            else:
                # Si no hay objetivos, movimiento aleatorio
                super().move(canvas_width, canvas_height)
        else:
            # Movimiento base si no hay simulación o método no disponible
            super().move(canvas_width, canvas_height)

    def chase_bacteria(self, bacteria: Bacteria):
        """Perseguir bacteria detectada"""
        # Calcular dirección hacia la bacteria
        dx = bacteria.x - self.x
        dy = bacteria.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            # Normalizar dirección
            dx /= dist
            dy /= dist
            
            # Fagocitos más agresivos son más rápidos
            aggression = self.genome.get('aggression_gene', 0.5)
            speed_gene = self.genome.get('speed_gene', 0.5)
            max_speed = SimulationConfig.MAX_SPEED * (1.0 + 0.5 * (speed_gene + aggression))
            
            turn_rate = SimulationConfig.TURN_RATE * (1.0 + speed_gene)
            
            # Suavizar giro hacia la bacteria
            self.vx += dx * turn_rate
            self.vy += dy * turn_rate
            self.normalize_velocity()
            
            # Aplicar velocidad
            self.vx *= max_speed
            self.vy *= max_speed
    
    def capture_bacteria(self, bacteria: Bacteria) -> bool:
        """Intentar capturar bacteria"""
        # Calcular distancia
        dx = bacteria.x - self.x
        dy = bacteria.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        # Capturar si está suficientemente cerca
        capture_radius = SimulationConfig.CAPTURE_RADIUS
        if dist < capture_radius:
            # Ganar energía al capturar (más si es agresivo)
            aggression = self.genome.get('aggression_gene', 0.5)
            energy_gain = SimulationConfig.ENERGY_GAIN * (1.0 + 0.5 * aggression)
            self.energy += energy_gain
            self.energy = min(200.0, self.energy)
            return True
        
        return False
    
    def reproduce(self) -> Optional['Phagocyte']:
        """Reproducción asexual (si tiene suficiente energía)"""
        if self.energy > 180:
            self.energy -= 80
            
            # Crear nuevo fagocito con mutación
            child_genome = self.genome.copy()
            
            # Mutación en genes
            for gene in child_genome:
                if random.random() < SimulationConfig.MUTATION_RATE:
                    child_genome[gene] += random.uniform(-0.1, 0.1)
                    child_genome[gene] = max(0.0, min(1.0, child_genome[gene]))
            
            child = Phagocyte(genome=child_genome)
            child.x = self.x + random.uniform(-30, 30)
            child.y = self.y + random.uniform(-30, 30)
            
            return child
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir fagocito a diccionario incluyendo propiedades específicas"""
        data = super().to_dict()
        data.update({
            'aggression_gene': self.genome.get('aggression_gene', 0.5)
        })
        return data