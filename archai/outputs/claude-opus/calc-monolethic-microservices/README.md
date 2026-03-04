# Calculator Microservices Architecture

This project demonstrates the transformation of a monolithic calculator application into a microservices architecture using FastAPI, Docker, and Kubernetes.

## Architecture Overview

The application is split into the following microservices:

### 1. API Gateway Service (Port 8000)
- **Purpose**: Routes requests to appropriate microservices
- **Features**: Load balancing, health checks, request routing
- **Endpoints**: `/api/calculate`, `/api/history`, `/health`

### 2. Calculator Service (Port 8001)
- **Purpose**: Handles mathematical calculations and expression parsing
- **Features**: Expression validation, calculation engine, error handling
- **Dependencies**: Communicates with History Service

### 3. History Service (Port 8002)
- **Purpose**: Manages calculation history storage and retrieval
- **Features**: Persistent storage, history management, data APIs
- **Storage**: JSON file persistence (configurable to database)

### 4. CLI Client
- **Purpose**: Command-line interface for user interaction
- **Features**: Interactive calculator, history viewing, health monitoring
- **Communication**: HTTP requests to API Gateway

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the project directory
2. Build and start all services:
```bash
docker-compose up --build
```

3. In another terminal, run the CLI client:
```bash
cd client
pip install -r requirements.txt
python cli_client.py
```

### Manual Setup

1. Start each service individually:

```bash
# Terminal 1 - History Service
cd services/history-service
pip install -r requirements.txt
python -m app.main

# Terminal 2 - Calculator Service
cd services/calculator-service
pip install -r requirements.txt
python -m app.main

# Terminal 3 - Gateway Service
cd services/gateway-service
pip install -r requirements.txt
python -m app.main

# Terminal 4 - CLI Client
cd client
pip install -r requirements.txt
python cli_client.py
```

### Using Kubernetes

1. Create namespace and deploy services:
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```

2. Forward gateway port:
```bash
kubectl port-forward -n calculator service/gateway-service 8000:8000
```

3. Run CLI client:
```bash
cd client
python cli_client.py http://localhost:8000
```

## Service Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   CLI Client    │────│   API Gateway   │
└─────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │                   │
            ┌───────▼────────┐  ┌──────▼──────┐
            │ Calculator     │  │  History    │
            │ Service        │──│  Service    │
            └────────────────┘  └─────────────┘
                                      │
                               ┌──────▼──────┐
                               │  JSON File  │
                               │  Storage    │
                               └─────────────┘
```

## API Endpoints

### Gateway Service (Port 8000)
- `POST /api/calculate` - Perform calculations
- `GET /api/history` - Get calculation history
- `DELETE /api/history` - Clear calculation history
- `GET /health` - Service health check

### Calculator Service (Port 8001)
- `POST /calculate` - Calculate expressions
- `GET /health` - Health check

### History Service (Port 8002)
- `POST /history` - Add calculation to history
- `GET /history` - Get all history
- `GET /history/last` - Get last result
- `DELETE /history` - Clear history
- `GET /health` - Health check

## Features

### Calculator Capabilities
- Basic arithmetic: `+`, `-`, `*`, `/`, `%`
- Exponentiation: `^` or `**`
- Parentheses for grouping
- `ans` keyword for last result
- Expression validation and error handling

### CLI Commands
- `help` - Show help message
- `history` - Display calculation history
- `clear` - Clear calculation history
- `health` - Check service status
- `exit`/`quit` - Exit application

### Example Usage
```
Calculator> 2 + 3 * 4
2 + 3 * 4 = 14.0 [14:30:25]

Calculator> ans ^ 2
ans ^ 2 = 196.0 [14:30:30]

Calculator> history
==================================================
CALCULATION HISTORY
==================================================
2 + 3 * 4 = 14.0 [14:30:25]
ans ^ 2 = 196.0 [14:30:30]
==================================================
```

## Configuration

### Environment Variables
- `GATEWAY_URL`: API Gateway URL (default: http://localhost:8000)
- `CALCULATOR_SERVICE_URL`: Calculator service URL
- `HISTORY_SERVICE_URL`: History service URL

### Docker Configuration
- Each service has its own Dockerfile
- docker-compose.yml for orchestration
- Volumes for data persistence
- Health checks for all services
- Network isolation

### Kubernetes Configuration
- Deployments for each service
- Services for internal communication
- PersistentVolumeClaim for history data
- ConfigMaps for configuration
- Horizontal Pod Autoscaling ready

## Monitoring and Health

All services expose `/health` endpoints for monitoring:
- Gateway health includes downstream service status
- Individual service health checks
- Docker Compose health checks
- Kubernetes liveness and readiness probes

## Development

### Adding New Features
1. Identify which service should handle the feature
2. Add API endpoints to the appropriate service
3. Update the Gateway routes if needed
4. Modify the CLI client if user interaction is required
5. Add tests for the new functionality

### Scaling Services
- Calculator Service: Can be scaled horizontally (stateless)
- History Service: Requires careful scaling (state management)
- Gateway Service: Can be scaled horizontally

### Data Persistence
- Current: JSON file storage
- Upgrade path: PostgreSQL, MongoDB, or other databases
- Volume mounts for data persistence

## Testing

### Unit Tests
Each service should have unit tests for:
- Business logic validation
- API endpoint functionality
- Error handling

### Integration Tests
- Service-to-service communication
- End-to-end workflows
- Database connectivity

### Load Testing
- Gateway routing performance
- Service response times
- Concurrent request handling

## Security Considerations

- Input validation at service boundaries
- Rate limiting at gateway level
- Service-to-service authentication
- Network segmentation
- Secret management for production

## Production Deployment

### Recommended Setup
1. Use Kubernetes for orchestration
2. Add monitoring (Prometheus/Grafana)
3. Implement logging (ELK stack)
4. Set up CI/CD pipelines
5. Configure auto-scaling
6. Add backup strategies for history data

### Performance Optimizations
- Redis caching for frequent calculations
- Database connection pooling
- Response compression
- CDN for static assets (if any)

This microservices architecture provides better scalability, maintainability, and separation of concerns compared to the original monolithic design.