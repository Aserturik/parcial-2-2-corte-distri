import os
import json
import pika
from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
auth = HTTPBasicAuth()

# Configuración
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'password123')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'messages')

# Usuarios para autenticación básica
users = {
    "admin": "password123",
    "user": "userpass"
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username
    return None

def get_rabbitmq_connection():
    """Establece conexión con RabbitMQ"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        return connection
    except Exception as e:
        logger.error(f"Error conectando a RabbitMQ: {e}")
        return None

def publish_message(message):
    """Publica mensaje en la cola de RabbitMQ"""
    connection = get_rabbitmq_connection()
    if not connection:
        return False
    
    try:
        channel = connection.channel()
        
        # Declarar la cola (se crea si no existe)
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        # Preparar el mensaje con timestamp
        message_data = {
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'source': 'api-service'
        }
        
        # Publicar mensaje
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hacer el mensaje persistente
            )
        )
        
        logger.info(f"Mensaje publicado: {message_data}")
        return True
        
    except Exception as e:
        logger.error(f"Error publicando mensaje: {e}")
        return False
    finally:
        if connection:
            connection.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'api-service',
        'version': '1.0'
    }
    
    # Verificar conexión con RabbitMQ (opcional, no falla si no conecta)
    try:
        connection = get_rabbitmq_connection()
        if connection:
            connection.close()
            health_status['rabbitmq'] = 'connected'
        else:
            health_status['rabbitmq'] = 'disconnected'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['rabbitmq'] = 'error'
        health_status['rabbitmq_error'] = str(e)
        health_status['status'] = 'degraded'
    
    # El servicio sigue siendo "healthy" aunque RabbitMQ no esté disponible
    # para que el healthcheck de Docker no falle constantemente
    return jsonify(health_status)

@app.route('/message', methods=['POST'])
@auth.login_required
def post_message():
    """Endpoint principal para recibir y enviar mensajes a RabbitMQ"""
    try:
        # Verificar que el contenido sea JSON
        if not request.is_json:
            return jsonify({'error': 'Content-Type debe ser application/json'}), 400
        
        data = request.get_json()
        
        # Validar que tenga contenido
        if not data or 'message' not in data:
            return jsonify({'error': 'El campo "message" es requerido'}), 400
        
        message = data['message']
        
        # Publicar mensaje en RabbitMQ
        if publish_message(message):
            return jsonify({
                'status': 'success',
                'message': 'Mensaje enviado correctamente',
                'timestamp': datetime.now().isoformat()
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Error enviando mensaje a RabbitMQ'
            }), 500
            
    except Exception as e:
        logger.error(f"Error en endpoint /message: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Error interno del servidor'
        }), 500

@app.route('/status', methods=['GET'])
@auth.login_required
def get_status():
    """Endpoint para verificar el estado de la conexión con RabbitMQ"""
    connection = get_rabbitmq_connection()
    if connection:
        connection.close()
        return jsonify({
            'rabbitmq_connection': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'rabbitmq_connection': 'disconnected',
            'timestamp': datetime.now().isoformat()
        }), 503

if __name__ == '__main__':
    logger.info("Iniciando API Service...")
    logger.info(f"RabbitMQ Host: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    logger.info(f"RabbitMQ Queue: {RABBITMQ_QUEUE}")
    
    app.run(host='0.0.0.0', port=5000, debug=False) 