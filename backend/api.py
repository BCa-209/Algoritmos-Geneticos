"""
API RESTful para la simulación de coevolución sin WebSockets
"""
import time
import threading
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from core.simulation import Simulation
from config import SimulationConfig

# Crear aplicación Flask
app = Flask(__name__, 
            static_folder='../frontend', 
            template_folder='../frontend',
            static_url_path='')

# Configurar CORS
CORS(app)

# Estado global de la simulación
simulation = None
simulation_lock = threading.Lock()
is_running = False
current_generation = 0
simulation_thread = None

# Caché para datos de simulación
simulation_cache = {
    'state': None,
    'stats': None,
    'last_update': None,
    'generation': 0
}

# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    """Página principal - sirve el frontend"""
    return render_template('index.html')

@app.route('/<path:path>')
def serve_frontend(path):
    """Servir archivos estáticos del frontend"""
    return send_from_directory(app.static_folder, path)

# ==================== ENDPOINTS DE API ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar estado del servicio"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'simulation_running': is_running,
        'current_generation': current_generation,
        'service': 'Coevolution Simulation API',
        'version': '1.0.0'
    })

@app.route('/api/parameters', methods=['GET'])
def get_parameters():
    """Obtener parámetros actuales o por defecto"""
    if simulation:
        return jsonify(simulation.get_parameters())
    return jsonify(SimulationConfig.get_default_parameters())

@app.route('/api/parameters', methods=['POST'])
def update_parameters():
    """Actualizar parámetros de simulación"""
    global simulation
    
    if not simulation:
        return jsonify({'error': 'No hay simulación activa'}), 400
    
    try:
        params = request.get_json()
        if not params:
            return jsonify({'error': 'No se proporcionaron parámetros'}), 400
        
        with simulation_lock:
            simulation.update_parameters(params)
        
        return jsonify({
            'status': 'success',
            'message': 'Parámetros actualizados',
            'parameters': simulation.get_parameters()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ==================== CONTROL DE SIMULACIÓN ====================

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    """Iniciar nueva simulación"""
    global simulation, simulation_thread, is_running
    
    try:
        with simulation_lock:
            # Detener simulación existente si hay una
            if simulation and is_running:
                simulation.stop()
                is_running = False
                if simulation_thread:
                    simulation_thread.join(timeout=2)
            
            # Crear nueva simulación
            simulation = Simulation()
            
            # Configurar parámetros si se proporcionan
            params = request.get_json()
            if params:
                simulation.update_parameters(params)
            
            # Limpiar caché
            global simulation_cache
            simulation_cache = {
                'state': None,
                'stats': None,
                'last_update': None,
                'generation': 0
            }
            
            # Iniciar hilo de simulación
            is_running = True
            simulation_thread = threading.Thread(
                target=run_simulation_loop,
                daemon=True
            )
            simulation_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Simulación iniciada',
            'parameters': simulation.get_parameters(),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/simulation/stop', methods=['POST'])
def stop_simulation():
    """Detener simulación"""
    global is_running
    
    if not simulation:
        return jsonify({'error': 'No hay simulación activa'}), 400
    
    with simulation_lock:
        simulation.stop()
        is_running = False
    
    return jsonify({
        'status': 'success', 
        'message': 'Simulación detenida',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/simulation/pause', methods=['POST'])
def pause_simulation():
    """Pausar simulación"""
    if not simulation:
        return jsonify({'error': 'No hay simulación activa'}), 400
    
    with simulation_lock:
        simulation.pause()
    
    return jsonify({
        'status': 'success', 
        'message': 'Simulación pausada',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/simulation/resume', methods=['POST'])
def resume_simulation():
    """Reanudar simulación"""
    global is_running
    
    if not simulation:
        return jsonify({'error': 'No hay simulación activa'}), 400
    
    with simulation_lock:
        simulation.resume()
        is_running = True
    
    return jsonify({
        'status': 'success', 
        'message': 'Simulación reanudada',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/simulation/reset', methods=['POST'])
def reset_simulation():
    """Reiniciar simulación"""
    global simulation
    
    if not simulation:
        return jsonify({'error': 'No hay simulación activa'}), 400
    
    with simulation_lock:
        simulation.reset()
    
    # Limpiar caché
    global simulation_cache
    simulation_cache = {
        'state': None,
        'stats': None,
        'last_update': None,
        'generation': 0
    }
    
    return jsonify({
        'status': 'success', 
        'message': 'Simulación reiniciada',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/simulation/step', methods=['POST'])
def step_simulation():
    """Ejecutar un paso de simulación"""
    if not simulation:
        return jsonify({'error': 'No hay simulación activa'}), 400
    
    with simulation_lock:
        simulation.step()
        current_gen = simulation.generation
        
        # Actualizar caché
        global simulation_cache
        simulation_cache['state'] = simulation.get_simulation_state()
        simulation_cache['stats'] = simulation.get_statistics()
        simulation_cache['last_update'] = time.time()
        simulation_cache['generation'] = current_gen
    
    return jsonify({
        'status': 'success',
        'message': 'Paso ejecutado',
        'generation': current_gen,
        'timestamp': datetime.now().isoformat()
    })

# ==================== OBTENCIÓN DE DATOS ====================

@app.route('/api/simulation/state', methods=['GET'])
def get_simulation_state():
    """Obtener estado actual de simulación"""
    if not simulation:
        return jsonify({'error': 'No hay simulación activa'}), 404
    
    with simulation_lock:
        # Usar caché si está disponible y es reciente (menos de 0.1 segundos)
        current_time = time.time()
        if (simulation_cache['state'] and 
            simulation_cache['last_update'] and 
            (current_time - simulation_cache['last_update']) < 0.1):
            state = simulation_cache['state']
        else:
            state = simulation.get_simulation_state()
            simulation_cache['state'] = state
            simulation_cache['last_update'] = current_time
            simulation_cache['generation'] = simulation.generation
    
    return jsonify(state)

@app.route('/api/simulation/stats', methods=['GET'])
def get_simulation_stats():
    """Obtener estadísticas de simulación"""
    if not simulation:
        return jsonify({'error': 'No hay simulación activa'}), 404
    
    with simulation_lock:
        # Usar caché si está disponible y es reciente (menos de 1 segundo)
        current_time = time.time()
        if (simulation_cache['stats'] and 
            simulation_cache['last_update'] and 
            (current_time - simulation_cache['last_update']) < 1.0):
            stats = simulation_cache['stats']
        else:
            stats = simulation.get_statistics()
            simulation_cache['stats'] = stats
            simulation_cache['last_update'] = current_time
    
    return jsonify(stats)

@app.route('/api/simulation/status', methods=['GET'])
def get_simulation_status():
    """Obtener estado general de simulación"""
    global is_running, current_generation
    
    if not simulation:
        return jsonify({
            'is_running': False,
            'message': 'No hay simulación activa',
            'timestamp': datetime.now().isoformat()
        })
    
    with simulation_lock:
        status = simulation.get_status()
        status.update({
            'is_running': is_running,
            'current_generation': current_generation,
            'timestamp': datetime.now().isoformat()
        })
    
    return jsonify(status)

@app.route('/api/simulation/updates', methods=['GET'])
def get_simulation_updates():
    """Obtener actualizaciones de simulación (para polling optimizado)"""
    if not simulation:
        return jsonify({'error': 'No hay simulación activa'}), 404
    
    # Obtener parámetros de la solicitud
    since_gen = request.args.get('since', type=int, default=0)
    include_state = request.args.get('state', type=str, default='true').lower() == 'true'
    include_stats = request.args.get('stats', type=str, default='false').lower() == 'true'
    
    with simulation_lock:
        current_gen = simulation.generation
        
        # Si no hay cambios desde la última consulta
        if current_gen <= since_gen:
            return jsonify({
                'has_updates': False,
                'current_generation': current_gen,
                'timestamp': datetime.now().isoformat()
            })
        
        # Preparar respuesta con datos actualizados
        response = {
            'has_updates': True,
            'current_generation': current_gen,
            'timestamp': datetime.now().isoformat()
        }
        
        if include_state:
            response['state'] = simulation.get_simulation_state()
        
        if include_stats:
            response['stats'] = simulation.get_statistics()
        
        # Limitar datos para optimizar
        if include_state and 'state' in response:
            state = response['state']
            if len(state.get('agents', {}).get('bacteria', [])) > 100:
                state['agents']['bacteria'] = state['agents']['bacteria'][:100]
            if len(state.get('agents', {}).get('phagocytes', [])) > 50:
                state['agents']['phagocytes'] = state['agents']['phagocytes'][:50]
    
    return jsonify(response)

# ==================== BUCLE DE SIMULACIÓN ====================

def run_simulation_loop():
    """Bucle principal de simulación en hilo separado"""
    global simulation, is_running, current_generation, simulation_cache
    
    try:
        while is_running and simulation:
            start_time = time.time()
            
            with simulation_lock:
                if not simulation.is_paused:
                    # Ejecutar paso de simulación
                    simulation.step()
                    current_generation = simulation.generation
                    
                    # Actualizar caché
                    simulation_cache['state'] = simulation.get_simulation_state()
                    simulation_cache['stats'] = simulation.get_statistics()
                    simulation_cache['last_update'] = time.time()
                    simulation_cache['generation'] = current_generation
            
            # Controlar FPS
            elapsed = time.time() - start_time
            target_time = 1.0 / SimulationConfig.FPS
            if elapsed < target_time:
                time.sleep(target_time - elapsed)
                
    except Exception as e:
        print(f"Error en bucle de simulación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        is_running = False

# ==================== INICIALIZACIÓN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Iniciando API de simulación de coevolución...")
    print(f"📁 Directorio actual: {os.getcwd()}")
    print(f"🔗 API disponible en: http://localhost:5000")
    print("=" * 60)
    
    # Crear directorios necesarios si no existen
    import os
    if not os.path.exists('frontend'):
        os.makedirs('frontend')
    
    # Ejecutar servidor
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)