# Proyecto Parcial 4 - Arquitectura de Microservicios

**Autor:** Alex Hernández

## Estructura de Archivos

```
docker-compose.yml
persistence.json
README.md
api-service/
    app.py
    Dockerfile
    requirements.txt
consumer-worker/
    Dockerfile
    requirements.txt
    worker.py
rabbitmq/
    enabled_plugins
    rabbitmq.conf
images/
```

- **API REST** en Flask que produce mensajes
- **Worker consumidor** que procesa mensajes desde RabbitMQ
- **Traefik** como reverse proxy
- **RabbitMQ** como broker de mensajes
- **Docker Compose** para orquestación
- **Persistencia** de datos en archivo JSON

## Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│   Traefik       │    │   API Service    │    │ Consumer Worker │
│  (Port 80/8080) │────│   (Flask)        │    │   (Python)      │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         │                        │                       │
         │              ┌─────────▼───────────────────────▼─────┐
         │              │                                       │
         └──────────────┤           RabbitMQ                    │
                        │       (Management UI)                 │
                        │                                       │
                        └───────────────────────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │                 │
                              │ persistence.json│
                              │   (Volumen)     │
                              │                 │
                              └─────────────────┘
```

## Servicios Implementados

### 1. API Service (Flask)
- **Puerto interno:** 5000
- **Ruta externa:** `/api/*` (via Traefik)
- **Autenticación:** Basic Auth
- **Endpoints:**
  - `POST /api/message` - Envía mensajes a RabbitMQ
  - `GET /api/health` - Check de salud
  - `GET /api/status` - Estado de conexión con RabbitMQ

### 2. Consumer Worker
- **Función:** Consume mensajes de la cola `messages`
- **Persistencia:** Guarda mensajes en `persistence.json`
- **Características:**
  - Reconexión automática
  - Manejo de errores
  - Límite de 1000 mensajes históricos

### 3. RabbitMQ
- **Puerto AMQP:** 5672
- **Management UI:** 15672 (acceso directo) o `/monitor` (via Traefik)
- **Credenciales:** admin/password123

### 4. Traefik
- **Dashboard:** Puerto 8080
- **Web:** Puerto 80
- **Enrutamiento:**
  - `/api/*` → API Service
  - `/monitor/*` → RabbitMQ Management

## Configuración y Uso

### Prerrequisitos
- Docker
- Docker Compose

### Iniciar el sistema

```bash
# Clonar el repositorio
git clone https://github.com/Aserturik/parcial-2-2-corte-distri.git
cd parcial-2-2-corte-distri

# Iniciar todos los servicios
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f
```

### Verificar servicios

```bash
# Estado de los contenedores
docker-compose ps

# Logs específicos
docker-compose logs api-service
docker-compose logs consumer-worker
docker-compose logs rabbitmq
docker-compose logs traefik
```

### Acceder a interfaces web

- **Traefik Dashboard:** <http://localhost:8080>
- **RabbitMQ Management:** <http://localhost/monitor> (admin/password123)
- **API Health Check:** <http://localhost/api/health>

## Testing de la API

### Endpoint POST /message - Publicar en Cola RabbitMQ

El endpoint principal `POST /api/message` permite enviar mensajes que serán publicados en la cola RabbitMQ `messages` para ser procesados por el worker consumidor.

#### Autenticación Básica Requerida

El endpoint está protegido con **HTTP Basic Authentication**. Las credenciales disponibles son:

| Usuario | Contraseña | Descripción |
|---------|------------|-------------|
| `admin` | `password123` | Usuario administrador |
| `user` | `userpass` | Usuario regular |

#### Formato del Mensaje

El endpoint espera un JSON con la siguiente estructura:
```json
{
  "message": "Tu mensaje aquí"
}
```

#### Ejemplos de Uso con curl

##### 1. Envío básico con usuario admin

```bash
curl -X POST http://localhost/api/message \
  -H "Content-Type: application/json" \
  -u admin:password123 \
  -d '{"message": "Hola desde la API!"}'
```

##### 2. Envío con usuario regular

```bash
curl -X POST http://localhost/api/message \
  -H "Content-Type: application/json" \
  -u user:userpass \
  -d '{"message": "Mensaje desde usuario regular"}'
```

##### 3. Mensaje más complejo

```bash
curl -X POST http://localhost/api/message \
  -H "Content-Type: application/json" \
  -u admin:password123 \
  -d '{
    "message": "Pedido #12345: Cliente solicita información sobre producto XYZ"
  }'
```

##### 4. Usando variables de entorno para seguridad

```bash
# Definir credenciales
export API_USER="admin"
export API_PASS="password123"

# Enviar mensaje
curl -X POST http://localhost/api/message \
  -H "Content-Type: application/json" \
  -u $API_USER:$API_PASS \
  -d '{"message": "Mensaje usando variables de entorno"}'
```

#### Respuestas del Endpoint

##### Respuesta Exitosa (201 Created)
```json
{
  "status": "success",
  "message": "Mensaje enviado correctamente",
  "timestamp": "2024-01-01T12:00:00.123456"
}
```

##### Error de Autenticación (401 Unauthorized)
```json
{
  "message": "The server could not verify that you are authorized to access the URL requested."
}
```

##### Error de Formato (400 Bad Request)
```json
{
  "error": "Content-Type debe ser application/json"
}
```

o

```json
{
  "error": "El campo \"message\" es requerido"
}
```

##### Error de Conexión RabbitMQ (500 Internal Server Error)
```json
{
  "status": "error",
  "message": "Error enviando mensaje a RabbitMQ"
}
```

#### Verificar que el Mensaje fue Procesado

Después de enviar un mensaje, puedes verificar que fue procesado correctamente:

```bash
# 1. Ver el archivo de persistencia
cat persistence.json | jq .

# 2. Ver logs del worker
docker-compose logs consumer-worker

# 3. Verificar cola en RabbitMQ Management UI
# Ir a: http://localhost/monitor -> Queues -> messages
```

### Otros Endpoints de la API

#### Verificar Estado de Conexión RabbitMQ

```bash
# Requiere autenticación
curl -u admin:password123 http://localhost/api/status
```

Respuesta:
```json
{
  "rabbitmq_connection": "connected",
  "timestamp": "2024-01-01T12:00:00.123456"
}
```

#### Health Check

```bash
# No requiere autenticación
curl http://localhost/api/health
```

Respuesta:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.123456"
}
```

### Script de Prueba Automatizada

Puedes crear un script bash para probar múltiples mensajes:

```bash
#!/bin/bash

echo "=== Probando API de Mensajes ==="

# Configuración
API_URL="http://localhost/api/message"
USER="admin"
PASS="password123"

# Array de mensajes de prueba
messages=(
  "Mensaje de prueba #1"
  "Pedido urgente: Cliente VIP"
  "Notificación: Sistema actualizado"
  "Alert: Revisar inventario"
)

# Enviar cada mensaje
for i in "${!messages[@]}"; do
  echo "Enviando mensaje $((i+1))..."
  
  curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -u "$USER:$PASS" \
    -d "{\"message\": \"${messages[i]}\"}" | jq .
  
  echo ""
  sleep 1
done

echo "=== Verificando persistencia ==="
cat persistence.json | jq .stats
```

## Estructura de Persistencia

Los mensajes se guardan en `persistence.json` con la siguiente estructura:

```json
{
  "metadata": {
    "created_at": "2024-01-01T12:00:00.000000",
    "worker_info": {
      "worker_id": "consumer-worker",
      "version": "1.0"
    }
  },
  "messages": [
    {
      "content": "Hola desde la API!",
      "timestamp": "2024-01-01T12:00:00.000000",
      "source": "api-service",
      "processed_at": "2024-01-01T12:00:01.000000",
      "worker_id": "consumer-worker",
      "delivery_tag": 1,
      "routing_key": "messages"
    }
  ],
  "stats": {
    "total_messages": 1,
    "last_updated": "2024-01-01T12:00:01.000000"
  }
}
```

## Características de Seguridad

### Autenticación API
- **Método:** HTTP Basic Auth
- **Usuarios disponibles:**
  - `admin:password123`
  - `user:userpass`

### Red Interna
- Red Docker personalizada `parcial-network`
- Comunicación interna entre servicios
- Solo puertos necesarios expuestos externamente

## Volúmenes y Persistencia

- **`messages-data`:** Volumen para datos del worker
- **`rabbitmq-data`:** Persistencia de datos RabbitMQ
- **`persistence.json`:** Archivo bind mount para mensajes procesados
- **`rabbitmq/`:** Archivos de configuración personalizados de RabbitMQ

### Configuración de RabbitMQ

El proyecto incluye configuración personalizada para RabbitMQ que permite el acceso correcto a través del path `/monitor`:

- **`rabbitmq/rabbitmq.conf`:** Configuración principal con `management.path_prefix = /monitor`
- **`rabbitmq/enabled_plugins`:** Plugins habilitados (management, prometheus, federation)

## Monitoreo y Troubleshooting

### Comandos útiles

```bash
# Reiniciar un servicio específico
docker-compose restart api-service

# Escalar el worker (múltiples instancias)
docker-compose up -d --scale consumer-worker=3

# Ver contenido del archivo de persistencia
cat persistence.json | jq .

# Acceder al contenedor del worker
docker-compose exec consumer-worker bash

# Limpiar todo y reiniciar
docker-compose down -v
docker-compose up -d
```

### Verificar conectividad

```bash
# Desde el contenedor API
docker-compose exec api-service ping rabbitmq

# Desde el worker
docker-compose exec consumer-worker ping rabbitmq
```

## Variables de Entorno

### API Service
- `RABBITMQ_HOST=rabbitmq`
- `RABBITMQ_PORT=5672`
- `RABBITMQ_USER=admin`
- `RABBITMQ_PASS=password123`
- `RABBITMQ_QUEUE=messages`

### Consumer Worker
- `RABBITMQ_HOST=rabbitmq`
- `RABBITMQ_PORT=5672`
- `RABBITMQ_USER=admin`
- `RABBITMQ_PASS=password123`
- `RABBITMQ_QUEUE=messages`

## Flujo de Datos

1. **Cliente** envía POST a `/api/message` con autenticación
2. **API Service** valida credenciales y payload
3. **API Service** publica mensaje en cola RabbitMQ `messages`
4. **Consumer Worker** consume mensaje de la cola
5. **Consumer Worker** procesa y guarda en `persistence.json`
6. **Worker** confirma procesamiento a RabbitMQ

## Desarrollo y Extensiones

### Agregar nuevos endpoints
1. Modificar `api-service/app.py`
2. Actualizar documentación
3. Rebuild: `docker-compose build api-service`

### Modificar lógica del worker
1. Editar `consumer-worker/worker.py`
2. Rebuild: `docker-compose build consumer-worker`

### Agregar nuevos servicios
1. Definir en `docker-compose.yml`
2. Configurar networking en `parcial-network`
3. Agregar labels de Traefik si es necesario

## Troubleshooting Común

### Worker no procesa mensajes
```bash
# Verificar logs
docker-compose logs consumer-worker

# Verificar cola en RabbitMQ
# Ir a http://localhost/monitor -> Queues -> messages
```

### API no responde
```bash
# Verificar estado del contenedor
docker-compose ps api-service

# Verificar logs
docker-compose logs api-service

# Probar conectividad interna
docker-compose exec api-service ping rabbitmq
```

### Traefik no enruta correctamente
```bash
# Verificar configuración de labels
docker-compose config

# Ver dashboard de Traefik
# http://localhost:8080
```

---

**Notas:** Este proyecto cumple con todos los requisitos del parcial incluyendo red personalizada, volúmenes nombrados, autenticación básica, y configuración de Traefik mediante labels.
