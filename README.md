# Proyecto Parcial 4 - Arquitectura de Microservicios

**Autor:** Alex Hernández

## Arquitectura

Sistema de microservicios con:

- **API REST** (Flask) que publica mensajes a RabbitMQ
- **Worker** que consume y procesa mensajes
- **Traefik** como reverse proxy
- **RabbitMQ** como broker de mensajes
- **Persistencia** en archivo JSON

## Servicios

| Servicio | Puerto | Acceso | Descripción |
|----------|--------|--------|-------------|
| **API Service** | 5000 | `/api/*` | Endpoints REST con autenticación |
| **RabbitMQ** | 5672 | `/monitor` | Broker de mensajes |
| **Traefik** | 80/8080 | Dashboard | Reverse proxy |
| **Worker** | - | - | Procesa mensajes en background |

## Inicio Rápido

```bash
# Clonar e iniciar
git clone https://github.com/Aserturik/parcial-2-2-corte-distri.git
cd parcial-2-2-corte-distri
docker-compose up -d

# Verificar estado
docker-compose ps
```

## Endpoints API

### Autenticación

- **Usuarios:** `admin:password123` / `user:userpass`
- **Método:** HTTP Basic Auth

### Endpoints Principales

```bash
# Enviar mensaje (requiere auth)
curl -X POST http://localhost/api/message \
  -H "Content-Type: application/json" \
  -u admin:password123 \
  -d '{"message": "Hola mundo!"}'

![alt text](image.png)

- Estos mensajes persisten en el fichero actual persistence.json:
![alt text](image-3.png)

# Health check API (sin auth)
curl http://localhost/api/health

![alt text](image-1.png)

# Estado RabbitMQ (requiere auth)
curl -u admin:password123 http://localhost/api/status
```
![alt text](image-2.png)

## Monitoreo y Salud

### Health Checks

- **API Service:** `http://localhost/api/health`
- **Consumer Worker:** `http://localhost:8080/health` (puerto interno)
- **Docker Health Checks:** Configurados para todos los servicios

### Logs en Tiempo Real

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Logs específicos
docker-compose logs -f api-service
docker-compose logs -f consumer-worker
docker-compose logs -f rabbitmq

# Estado de salud de contenedores
docker-compose ps
```

### Métricas y Estadísticas

```bash
# Ver estadísticas de mensajes procesados
cat persistence.json | jq .stats
![alt text](image-4.png)

# Estado detallado de RabbitMQalt text
curl -u admin:password123 http://localhost/api/status
![alt text](image-5.png)

# Health check completo del API
curl http://localhost/api/health | jq
```
![alt text](image-6.png)

## Acceso Web

- **Traefik Dashboard:** <http://localhost:8080>
  ![alt text](image-7.png)
- **RabbitMQ Management:** <http://localhost/monitor> (admin/password123)
  ![alt text](image-8.png)
- **API Health:** <http://localhost/api/health>
![alt text](image-9.png)

## Flujo de Datos

1. Cliente → API (`/api/message`)
2. API → RabbitMQ (cola `messages`)
3. Worker → Consume mensajes
4. Worker → Guarda en `persistence.json`

## Comandos Útiles

```bash
# Ver logs
docker-compose logs -f consumer-worker

# Verificar mensajes procesados
cat persistence.json | jq .stats

# Reiniciar servicio
docker-compose restart api-service

# Limpiar y reiniciar
docker-compose down -v && docker-compose up -d
```

## Troubleshooting

### Monitoreo y Diagnóstico

```bash
# Verificar estado de salud de todos los servicios
docker-compose ps

# Health checks específicos
curl http://localhost/api/health
curl http://localhost:8080/health  # Worker (puerto interno)

# Verificar logs en tiempo real
docker-compose logs -f

# Ver mensajes procesados y estadísticas
cat persistence.json | jq
```

### Problemas Comunes

- **API no responde:** `docker-compose logs api-service`
- **Worker no procesa:** Verificar cola en RabbitMQ Management UI
- **Traefik no enruta:** Revisar dashboard en puerto 8080
- **Health checks fallan:** `docker-compose ps` muestra estado unhealthy
