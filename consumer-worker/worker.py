import os
import json
import pika
import time
import logging
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'password123')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'messages')
PERSISTENCE_FILE = '/app/data/persistence.json'

def get_rabbitmq_connection():
    """Establece conexión con RabbitMQ con reintentos"""
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(parameters)
            logger.info("Conexión exitosa a RabbitMQ")
            return connection
        except Exception as e:
            logger.error(f"Intento {attempt + 1}/{max_retries} falló: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                logger.error("No se pudo conectar a RabbitMQ después de todos los reintentos")
                raise

def load_persistence_data():
    """Carga los datos existentes del archivo de persistencia"""
    try:
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(PERSISTENCE_FILE), exist_ok=True)
        
        if os.path.exists(PERSISTENCE_FILE) and os.path.getsize(PERSISTENCE_FILE) > 0:
            with open(PERSISTENCE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Datos cargados: {len(data.get('messages', []))} mensajes existentes")
                return data
        else:
            # Crear estructura inicial si el archivo no existe o está vacío
            initial_data = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "worker_info": {
                        "worker_id": os.getenv('HOSTNAME', 'unknown'),
                        "version": "1.0"
                    }
                },
                "messages": [],
                "stats": {
                    "total_messages": 0,
                    "last_updated": None
                }
            }
            return initial_data
    except Exception as e:
        logger.error(f"Error cargando datos de persistencia: {e}")
        return {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "error": str(e)
            },
            "messages": [],
            "stats": {
                "total_messages": 0,
                "last_updated": None
            }
        }

def save_persistence_data(data):
    """Guarda los datos en el archivo de persistencia"""
    try:
        # Actualizar estadísticas
        data["stats"]["total_messages"] = len(data["messages"])
        data["stats"]["last_updated"] = datetime.now().isoformat()
        
        # Escribir al archivo con formato bonito
        with open(PERSISTENCE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Datos guardados en {PERSISTENCE_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Error guardando datos de persistencia: {e}")
        return False

def add_message_to_persistence(message_data):
    """Agrega un nuevo mensaje al archivo de persistencia"""
    try:
        # Cargar datos existentes
        persistence_data = load_persistence_data()
        
        # Agregar el nuevo mensaje
        persistence_data["messages"].append(message_data)
        
        # Mantener solo los últimos 1000 mensajes para evitar que el archivo crezca demasiado
        if len(persistence_data["messages"]) > 1000:
            persistence_data["messages"] = persistence_data["messages"][-1000:]
            logger.info("Archivo de persistencia recortado a los últimos 1000 mensajes")
        
        # Guardar los datos actualizados
        return save_persistence_data(persistence_data)
        
    except Exception as e:
        logger.error(f"Error agregando mensaje a persistencia: {e}")
        return False

def process_message(ch, method, properties, body):
    """Procesa mensajes recibidos de RabbitMQ"""
    try:
        # Decodificar mensaje JSON
        message_data = json.loads(body.decode('utf-8'))
        logger.info(f"Mensaje recibido: {message_data}")
        
        # Agregar información adicional del procesamiento
        message_data['processed_at'] = datetime.now().isoformat()
        message_data['worker_id'] = os.getenv('HOSTNAME', 'unknown')
        message_data['delivery_tag'] = method.delivery_tag
        message_data['routing_key'] = method.routing_key
        
        # Guardar mensaje en persistencia
        if add_message_to_persistence(message_data):
            # Confirmar procesamiento del mensaje
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Mensaje procesado y guardado en persistencia")
        else:
            # Rechazar mensaje si no se pudo guardar
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            logger.error("Error procesando mensaje, reencolar")
            
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON: {e}")
        # Rechazar mensaje con formato inválido (no reencolar)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        # Rechazar mensaje y reencolar para reintento
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_consumer():
    """Inicia el consumidor de mensajes"""
    logger.info("Iniciando Consumer Worker...")
    logger.info(f"RabbitMQ Host: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    logger.info(f"RabbitMQ Queue: {RABBITMQ_QUEUE}")
    logger.info(f"Persistence File: {PERSISTENCE_FILE}")
    
    # Inicializar archivo de persistencia si es necesario
    persistence_data = load_persistence_data()
    save_persistence_data(persistence_data)
    
    while True:
        try:
            # Establecer conexión
            connection = get_rabbitmq_connection()
            channel = connection.channel()
            
            # Declarar la cola (asegurar que existe)
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            
            # Configurar QoS para procesar un mensaje a la vez
            channel.basic_qos(prefetch_count=1)
            
            # Configurar el consumidor
            channel.basic_consume(
                queue=RABBITMQ_QUEUE,
                on_message_callback=process_message
            )
            
            logger.info("Esperando mensajes. Para salir presiona CTRL+C")
            
            # Iniciar consumo
            channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Interrupción recibida, cerrando...")
            if 'channel' in locals():
                channel.stop_consuming()
            if 'connection' in locals():
                connection.close()
            break
            
        except Exception as e:
            logger.error(f"Error en el consumidor: {e}")
            logger.info("Reintentando en 10 segundos...")
            time.sleep(10)

if __name__ == '__main__':
    start_consumer() 