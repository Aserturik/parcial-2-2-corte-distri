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

# Health check (sin auth)
curl http://localhost/api/health

# Estado RabbitMQ (requiere auth)
curl -u admin:password123 http://localhost/api/status
```

## Acceso Web

- **Traefik Dashboard:** <http://localhost:8080>
- **RabbitMQ Management:** <http://localhost/monitor> (admin/password123)
- **API Health:** <http://localhost/api/health>

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

- **API no responde:** `docker-compose logs api-service`
- **Worker no procesa:** Verificar cola en RabbitMQ Management UI
- **Traefik no enruta:** Revisar dashboard en puerto 8080
