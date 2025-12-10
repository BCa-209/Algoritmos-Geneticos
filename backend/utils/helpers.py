"""
Funciones auxiliares para la simulación
"""
import math
import random
import numpy as np
from typing import Tuple, List, Dict, Any

def euclidean_distance(point1: Tuple[float, float], 
                      point2: Tuple[float, float]) -> float:
    """Calcular distancia euclidiana entre dos puntos"""
    x1, y1 = point1
    x2, y2 = point2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def normalize_vector(vector: Tuple[float, float]) -> Tuple[float, float]:
    """Normalizar vector a longitud 1"""
    x, y = vector
    length = math.sqrt(x**2 + y**2)
    if length > 0:
        return (x / length, y / length)
    return (0.0, 0.0)

def limit_vector(vector: Tuple[float, float], 
                max_length: float) -> Tuple[float, float]:
    """Limitar longitud de vector a máximo dado"""
    x, y = vector
    length = math.sqrt(x**2 + y**2)
    if length > max_length:
        factor = max_length / length
        return (x * factor, y * factor)
    return (x, y)

def random_point_in_circle(center: Tuple[float, float], 
                          radius: float) -> Tuple[float, float]:
    """Generar punto aleatorio dentro de círculo"""
    cx, cy = center
    angle = random.uniform(0, 2 * math.pi)
    r = random.uniform(0, radius)
    x = cx + r * math.cos(angle)
    y = cy + r * math.sin(angle)
    return (x, y)

def rgb_to_hex(color: Tuple[int, int, int]) -> str:
    """Convertir color RGB a formato HEX"""
    r, g, b = color
    return f"#{r:02x}{g:02x}{b:02x}"

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convertir color HEX a RGB"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)

def calculate_color_brightness(color: Tuple[int, int, int]) -> float:
    """Calcular brillo de color (0-1)"""
    r, g, b = color
    # Fórmula de luminosidad relativa
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0

def interpolate_color(color1: Tuple[int, int, int], 
                     color2: Tuple[int, int, int], 
                     t: float) -> Tuple[int, int, int]:
    """Interpolar entre dos colores"""
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    
    return (r, g, b)

def calculate_average_color(colors: List[Tuple[int, int, int]]) -> Tuple[int, int, int]:
    """Calcular color promedio de una lista de colores"""
    if not colors:
        return (128, 128, 128)
    
    r_sum = sum(c[0] for c in colors)
    g_sum = sum(c[1] for c in colors)
    b_sum = sum(c[2] for c in colors)
    
    n = len(colors)
    return (r_sum // n, g_sum // n, b_sum // n)

def normalize_value(value: float, 
                   min_val: float, 
                   max_val: float,
                   new_min: float = 0.0,
                   new_max: float = 1.0) -> float:
    """Normalizar valor de un rango a otro"""
    if max_val - min_val == 0:
        return new_min
    return ((value - min_val) / (max_val - min_val)) * (new_max - new_min) + new_min

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Limitar valor entre mínimo y máximo"""
    return max(min_val, min(max_val, value))

def random_normal(mu: float = 0.0, sigma: float = 1.0) -> float:
    """Generar número aleatorio con distribución normal"""
    return np.random.normal(mu, sigma)

def random_exponential(lam: float = 1.0) -> float:
    """Generar número aleatorio con distribución exponencial"""
    return random.expovariate(lam)

def calculate_angle(point1: Tuple[float, float], 
                   point2: Tuple[float, float]) -> float:
    """Calcular ángulo entre dos puntos en radianes"""
    x1, y1 = point1
    x2, y2 = point2
    return math.atan2(y2 - y1, x2 - x1)

def rotate_point(point: Tuple[float, float], 
                angle: float, 
                center: Tuple[float, float] = (0, 0)) -> Tuple[float, float]:
    """Rotar punto alrededor de centro dado"""
    px, py = point
    cx, cy = center
    
    # Translate point to origin
    px -= cx
    py -= cy
    
    # Rotate point
    cos_theta = math.cos(angle)
    sin_theta = math.sin(angle)
    x_new = px * cos_theta - py * sin_theta
    y_new = px * sin_theta + py * cos_theta
    
    # Translate point back
    return (x_new + cx, y_new + cy)