# Proyecto Parcial 4 - Arquitectura de Microservicios

**Autor:** Alex Hernández

## Descripción

Este proyecto implementa una arquitectura completa de microservicios local que incluye:

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
- **Management UI:** 15672
- **Ruta externa:** `/monitor/*` (via Traefik)
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
git clone <repository-url>
cd parcial-4

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

- **Traefik Dashboard:** http://localhost:8080
- **RabbitMQ Management:** http://localhost/monitor (admin/password123)
- **API Health Check:** http://localhost/api/health

## Testing de la API

### Enviar un mensaje

```bash
# Usando curl con autenticación básica
curl -X POST http://localhost/api/message \
  -H "Content-Type: application/json" \
  -u admin:password123 \
  -d '{"message": "Hola desde la API!"}'

# Respuesta esperada:
# {
#   "status": "success",
#   "message": "Mensaje enviado correctamente",
#   "timestamp": "2024-01-01T12:00:00.000000"
# }
```

### Verificar estado

```bash
# Estado de la API
curl -u admin:password123 http://localhost/api/status

# Health check (sin autenticación)
curl http://localhost/api/health
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
