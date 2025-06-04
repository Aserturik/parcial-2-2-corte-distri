import os
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time

logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            try:
                # Verificar que el archivo de persistencia existe y es legible
                persistence_file = '/app/data/persistence.json'
                health_data = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'service': 'consumer-worker',
                    'version': '1.0'
                }
                
                if os.path.exists(persistence_file):
                    # Leer estadísticas del archivo
                    try:
                        with open(persistence_file, 'r') as f:
                            data = json.load(f)
                            health_data['persistence'] = {
                                'file_exists': True,
                                'total_messages': data.get('stats', {}).get('total_messages', 0),
                                'last_updated': data.get('stats', {}).get('last_updated', 'never')
                            }
                    except Exception as e:
                        health_data['persistence'] = {
                            'file_exists': True,
                            'error': str(e)
                        }
                        health_data['status'] = 'degraded'
                else:
                    health_data['persistence'] = {
                        'file_exists': False
                    }
                    health_data['status'] = 'degraded'
                
                # Respuesta HTTP
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(health_data, indent=2).encode())
                
            except Exception as e:
                # Error interno
                error_data = {
                    'status': 'unhealthy',
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error_data, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Silenciar logs del servidor HTTP para no contaminar logs del worker
        pass

def start_health_server():
    """Inicia el servidor de salud en un hilo separado"""
    try:
        server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
        logger.info("Servidor de salud iniciado en puerto 8080")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Error iniciando servidor de salud: {e}")

def start_health_server_thread():
    """Inicia el servidor de salud en background"""
    health_thread = Thread(target=start_health_server, daemon=True)
    health_thread.start()
    return health_thread
