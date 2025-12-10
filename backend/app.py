
import os
import sys

# Añadir el directorio actual al path para imports correctos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import numpy as np
import time
import threading
from datetime import datetime

# Importaciones locales
from core.simulation import Simulation
from config import get_simulation_config  # Replace with the actual name available in config.py

# Crear la aplicación Flask
app = Flask(__name__, 
            static_folder='../frontend', 
            template_folder='../frontend',
            static_url_path='')

app.config['SECRET_KEY'] = 'coeva-secret-key-2024'

# Configurar CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Configurar SocketIO con Eventlet
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=False
)

# Estado global de la simulación
simulation = None
simulation_thread = None
is_running = False
current_generation = 0

# Bloqueo para acceso thread-safe
simulation_lock = threading.Lock()

# Ruta principal - redirige al frontend
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para archivos estáticos
@app.route('/<path:filename>')
def serve_frontend(filename):
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    try:
        return send_from_directory(frontend_path, filename)
    except:
        return "Archivo no encontrado", 404

# Ruta para salud del servidor
@app.route('/health')
def health_check():
    """Endpoint de salud del servicio"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "simulation_running": is_running,
        "generation": current_generation,
        "service": "Coevolution Simulation API",
        "version": "1.0.0"
    })

@app.route('/api/parameters')
def get_parameters():
    """Obtener parámetros actuales de simulación"""
    if simulation:
        return jsonify(simulation.get_parameters())
    return jsonify(SimulationConfig.get_default_parameters())

@app.route('/api/stats')
def get_stats():
    """Obtener estadísticas actuales"""
    if simulation:
        return jsonify(simulation.get_statistics())
    return jsonify({"error": "No simulation running"}), 404

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Manejar conexión de cliente WebSocket"""
    print(f"Cliente conectado: {request.sid}")
    emit('connection_status', {
        'status': 'connected',
        'message': 'Conectado al servidor de simulación',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Manejar desconexión de cliente WebSocket"""
    print(f"Cliente desconectado: {request.sid}")

@socketio.on('start_simulation')
def handle_start_simulation(data=None):
    """Iniciar nueva simulación"""
    global simulation, simulation_thread, is_running
    
    try:
        print("Iniciando simulación con parámetros por defecto")
        
        with simulation_lock:
            # Detener simulación existente si hay una
            if simulation and is_running:
                simulation.stop()
                is_running = False
                if simulation_thread:
                    simulation_thread.join(timeout=2)
            
            # Crear nueva simulación
            simulation = Simulation()
            
            # Iniciar hilo de simulación
            is_running = True
            simulation_thread = threading.Thread(
                target=run_simulation_loop,
                daemon=True
            )
            simulation_thread.start()
        
        emit('simulation_started', {
            'status': 'success',
            'message': 'Simulación iniciada con parámetros por defecto',
            'parameters': simulation.get_parameters(),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"Error iniciando simulación: {e}")
        import traceback
        traceback.print_exc()
        
        emit('error', {
            'code': 'SIMULATION_ERROR',
            'message': f'Error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('update_parameters')
def handle_update_parameters(data):
    """Actualizar parámetros en tiempo real"""
    global simulation
    
    if not simulation or not is_running:
        emit('error', {
            'code': 'NO_SIMULATION',
            'message': 'No hay simulación activa',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    try:
        parameters = data.get('parameters', {})
        
        with simulation_lock:
            simulation.update_parameters(parameters)
        
        emit('parameters_updated', {
            'status': 'success',
            'message': 'Parámetros actualizados',
            'parameters': simulation.get_parameters(),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        emit('error', {
            'code': 'PARAMETER_ERROR',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('control_command')
def handle_control_command(data):
    """Manejar comandos de control"""
    global simulation, is_running
    
    command = data.get('command', '').lower()
    
    if not simulation:
        emit('error', {
            'code': 'NO_SIMULATION',
            'message': 'No hay simulación activa',
            'timestamp': datetime.now().isoformat()
        })
        return
    
    try:
        with simulation_lock:
            if command == 'pause':
                simulation.pause()
                is_running = False
                message = 'Simulación pausada'
            elif command == 'resume':
                simulation.resume()
                is_running = True
                message = 'Simulación reanudada'
            elif command == 'reset':
                simulation.reset()
                message = 'Simulación reiniciada'
            elif command == 'step':
                simulation.step()
                message = 'Paso de simulación ejecutado'
            elif command == 'stop':
                simulation.stop()
                is_running = False
                message = 'Simulación detenida'
            else:
                raise ValueError(f"Comando no reconocido: {command}")
        
        emit('command_executed', {
            'status': 'success',
            'command': command,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'is_running': is_running
        })
        
    except Exception as e:
        emit('error', {
            'code': 'CONTROL_ERROR',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('get_status')
def handle_get_status():
    """Obtener estado actual de simulación"""
    global simulation, is_running, current_generation
    
    if simulation:
        status = simulation.get_status()
        status['is_running'] = is_running
        status['current_generation'] = current_generation
        
        emit('status_update', status)
    else:
        emit('status_update', {
            'is_running': False,
            'message': 'No hay simulación activa',
            'timestamp': datetime.now().isoformat()
        })

def run_simulation_loop():
    """Bucle principal de simulación en hilo separado"""
    global simulation, is_running, current_generation
    
    try:
        while is_running and simulation:
            with simulation_lock:
                if not simulation.is_paused:
                    # Ejecutar paso de simulación
                    simulation.step()
                    current_generation = simulation.generation
                    
                    # Preparar datos para enviar
                    simulation_data = simulation.get_simulation_state()
                    
                    # Enviar actualización a través de WebSocket
                    socketio.emit('simulation_update', {
                        'event': 'simulation_update',
                        'data': simulation_data,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Enviar estadísticas cada 10 generaciones
                    if current_generation % 10 == 0:
                        stats = simulation.get_statistics()
                        socketio.emit('statistics_update', {
                            'event': 'statistics_update',
                            'data': stats,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    # Notificar generación completa
                    socketio.emit('generation_complete', {
                        'event': 'generation_complete',
                        'data': {
                            'generation': current_generation,
                            'best_fitness': simulation.get_best_fitness(),
                            'avg_fitness': simulation.get_average_fitness()
                        },
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Controlar FPS
            time.sleep(1.0 / SimulationConfig.FPS)
            
    except Exception as e:
        print(f"Error en bucle de simulación: {e}")
        import traceback
        traceback.print_exc()
        socketio.emit('error', {
            'code': 'SIMULATION_LOOP_ERROR',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        })
    finally:
        is_running = False

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Iniciando servidor de simulación de coevolución...")
    print(f"📁 Directorio actual: {os.getcwd()}")
    print(f"📂 Backend path: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"🔌 WebSocket usando: eventlet")
    print("=" * 60)
    
    # Verificar existencia de archivos
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
    if os.path.exists(frontend_path):
        print(f"✅ Frontend encontrado en: {frontend_path}")
    else:
        print(f"⚠️  Frontend no encontrado en: {frontend_path}")
    
    # Iniciar servidor con SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,
        log_output=True
    )