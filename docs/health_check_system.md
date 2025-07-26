# Health Check System Documentation

## Overview

The Expense Analyser API implements a comprehensive health check system following industry standards for monitoring, alerting, and container orchestration. The system provides multiple endpoints for different use cases and monitoring scenarios.

## Health Check Endpoints

### 1. Comprehensive Health Check

**Endpoint:** `GET /api/v1/health` or `GET /health`

**Purpose:** Complete system health assessment including all dependencies

**Parameters:**
- `details` (boolean, optional): Include detailed component information (default: false)

**Response Statuses:**
- `200 OK`: System is healthy or degraded
- `503 Service Unavailable`: System is unhealthy

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-07-26T12:00:00Z",
  "duration_seconds": 0.156,
  "version": "0.1.0",
  "environment": "production",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "configuration": "healthy",
    "llm_providers": "healthy",
    "storage": "healthy"
  }
}
```

**With Details (`?details=true`):**
```json
{
  "status": "healthy",
  "timestamp": "2023-07-26T12:00:00Z",
  "duration_seconds": 0.156,
  "version": "0.1.0",
  "environment": "production",
  "components": {
    "database": {
      "status": "healthy",
      "checked_at": "2023-07-26T12:00:00Z",
      "version": "PostgreSQL 16.0",
      "connection_pool_size": 10,
      "tables_count": 8,
      "key_tables_present": true
    },
    "redis": {
      "status": "healthy",
      "checked_at": "2023-07-26T12:00:00Z",
      "version": "7.0.0",
      "used_memory_human": "2.1M",
      "connected_clients": 1,
      "uptime_in_seconds": 86400
    }
  }
}
```

### 2. Readiness Probe

**Endpoint:** `GET /api/v1/health/ready` or `GET /ready`

**Purpose:** Kubernetes-style readiness probe for load balancers and traffic routing

**Use Cases:**
- Kubernetes readiness probes
- Load balancer health checks
- Determining when to start sending traffic after deployment

**Response Statuses:**
- `200 OK`: Ready to receive traffic
- `503 Service Unavailable`: Not ready

**Example Response:**
```json
{
  "status": "ready",
  "timestamp": "2023-07-26T12:00:00Z",
  "duration_seconds": 0.045,
  "checks": {
    "database": "healthy",
    "configuration": "healthy"
  }
}
```

### 3. Liveness Probe

**Endpoint:** `GET /api/v1/health/live` or `GET /live`

**Purpose:** Kubernetes-style liveness probe for container restart decisions

**Use Cases:**
- Kubernetes liveness probes
- Basic monitoring to detect if the application needs restart
- Automated recovery systems

**Response Statuses:**
- `200 OK`: Application is alive (almost always)
- `503 Service Unavailable`: Application is dead (very rare)

**Example Response:**
```json
{
  "status": "alive",
  "timestamp": "2023-07-26T12:00:00Z",
  "uptime_seconds": 86400,
  "version": "0.1.0"
}
```

### 4. Simple Status Check

**Endpoint:** `GET /api/v1/health/status`

**Purpose:** Lightweight status check with minimal dependencies

**Response:** Always `200 OK` unless application is completely unresponsive

**Example Response:**
```json
{
  "status": "ok",
  "service": "expense-analyser-api",
  "version": "0.1.0"
}
```

### 5. Legacy Ping

**Endpoint:** `GET /api/v1/ping` or `GET /ping`

**Purpose:** Basic connectivity testing and backward compatibility

**Example Response:**
```json
{
  "ping": "pong"
}
```

## Health Status Levels

### 1. Healthy
- All components are functioning normally
- Application is fully operational
- All features available

### 2. Degraded
- Some non-critical components have issues
- Application is operational but with reduced functionality
- Examples:
  - Redis cache unavailable (falls back to in-memory)
  - Non-critical configuration warnings
  - LLM provider issues but fallback available

### 3. Unhealthy
- Critical components are failing
- Application may not function properly
- Examples:
  - Database connection failed
  - Critical configuration missing
  - Storage unavailable

## Component Checks

### Database
- **Checks:** Connectivity, basic operations, schema validation
- **Details:** Version, connection pool size, table count, key tables present
- **Critical:** Yes - application cannot function without database

### Redis Cache
- **Checks:** Connectivity, basic operations (set/get/delete)
- **Details:** Version, memory usage, connected clients, uptime
- **Critical:** No - falls back to in-memory cache
- **Degraded Conditions:** Redis unavailable, connection issues

### Configuration
- **Checks:** Required settings, security configurations, environment-specific validations
- **Details:** Environment, LLM provider, CORS setup, critical flags
- **Critical:** Yes for essential settings
- **Issues Checked:**
  - Default secret key in production
  - Missing LLM API keys for configured provider
  - Missing required database URL

### LLM Providers
- **Checks:** API key presence and format validation
- **Details:** Default provider, configured providers status
- **Critical:** Yes - application needs LLM for receipt processing
- **Providers Supported:** OpenAI (GPT), Google Gemini

### Storage
- **Checks:** Upload directory existence, write permissions, disk space
- **Details:** Directory path, writability, available space
- **Critical:** Yes - application needs storage for receipt uploads
- **Warnings:** Low disk space (< 100MB)

## Monitoring Integration

### Prometheus Metrics
The health endpoints return structured data that can be easily converted to Prometheus metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'expense-analyser'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /api/v1/health
    params:
      details: ['true']
    scrape_interval: 30s
```

### Kubernetes Probes

```yaml
# deployment.yaml
spec:
  containers:
  - name: expense-analyser-api
    livenessProbe:
      httpGet:
        path: /live
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    
    readinessProbe:
      httpGet:
        path: /ready
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 2
```

### Load Balancer Configuration

```nginx
# nginx.conf
upstream expense_api {
    server api1:8000;
    server api2:8000;
}

location /health {
    proxy_pass http://expense_api/health;
    proxy_set_header Host $host;
}

# Health check for upstream
location /api/health_check {
    access_log off;
    proxy_pass http://expense_api/ready;
    proxy_connect_timeout 1s;
    proxy_timeout 1s;
}
```

### Docker Compose Health Checks

```yaml
# docker-compose.yml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Alerting Guidelines

### Critical Alerts (Immediate Response)
- Health status is "unhealthy"
- Database connectivity issues
- Storage unavailable
- Application not responding to liveness probe

### Warning Alerts (Monitor)
- Health status is "degraded" 
- Redis cache unavailable
- Low disk space
- LLM provider issues
- Configuration warnings

### Monitoring Queries

```promql
# Application is unhealthy
expense_analyser_health_status{status="unhealthy"} == 1

# Database issues
expense_analyser_component_status{component="database",status!="healthy"} == 1

# Response time too high
expense_analyser_health_duration_seconds > 5

# Any component degraded
expense_analyser_component_status{status="degraded"} == 1
```

## Security Considerations

1. **Information Disclosure:** Health endpoints may reveal system information
   - Use `details=false` for external monitoring
   - Consider authentication for detailed health checks in production

2. **Rate Limiting:** Health endpoints should be exempt from rate limiting
   - Configure monitoring tools accordingly
   - Avoid impacting legitimate health checks

3. **Network Access:** 
   - Health endpoints should be accessible to monitoring systems
   - Consider separate network interfaces for health checks

## Performance Impact

- **Simple Status:** < 1ms - No external dependencies
- **Liveness:** < 5ms - Minimal checks
- **Readiness:** < 50ms - Database connectivity check
- **Full Health:** < 200ms - All component checks
- **Detailed Health:** < 300ms - All checks with metadata

## Best Practices

1. **Use appropriate endpoints for each use case:**
   - Kubernetes liveness: `/live`
   - Kubernetes readiness: `/ready`
   - Load balancer: `/ready` or `/health`
   - Monitoring/alerting: `/health?details=true`
   - Simple connectivity: `/ping`

2. **Configure appropriate timeouts:**
   - Liveness: 3-5 seconds
   - Readiness: 2-3 seconds
   - Full health: 5-10 seconds

3. **Set reasonable check intervals:**
   - Liveness: 10-30 seconds
   - Readiness: 5-10 seconds
   - Monitoring: 30-60 seconds

4. **Monitor health check performance:**
   - Alert if health checks take too long
   - Track health check success rates
   - Monitor false positives/negatives

## Troubleshooting

### Health Check Always Returns Unhealthy
1. Check database connectivity
2. Verify configuration settings
3. Check storage permissions
4. Review application logs

### Health Check Times Out
1. Check database performance
2. Verify Redis connectivity
3. Review system resources
4. Check network connectivity

### False Positive Alerts
1. Adjust failure thresholds
2. Increase timeout values
3. Review component check logic
4. Check for intermittent issues

This comprehensive health check system ensures reliable monitoring and helps maintain high availability of the Expense Analyser API.
