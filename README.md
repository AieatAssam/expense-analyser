# Expense Analyser

## Docker Setup

This project uses Docker Compose to manage its infrastructure. The current setup includes:

- PostgreSQL database service for data storage
- (Upcoming) FastAPI backend service for the application API

### Prerequisites

- Docker and Docker Compose installed on your system
- Copy `.env.template` to `.env` and update the values as needed

### Getting Started

1. Clone the repository:

```bash
git clone <repository-url>
cd expense-analyser
```

2. Set up environment variables:

```bash
cp .env.template .env
# Edit .env file with your Auth0, database, and API key settings
# Note: Both frontend and backend use the SAME Auth0 environment variables (no REACT_APP_ prefix needed)
```

3. Validate your environment configuration:

```bash
python3 validate_env.py
```

4. Start the Docker containers:

```bash
docker compose up -d
```

5. Verify the database is running:

```bash
docker compose ps
```

### Persistent Data

The Docker Compose configuration includes named volumes for:

- PostgreSQL data: `expense_analyser_postgres_data`
- (Upcoming) Receipt uploads: `expense_analyser_receipt_uploads`

These volumes ensure data persistence across container restarts.

### Networking

All services are connected through a bridge network named `expense_analyser_network`.

### Environment Variables

Key environment variables include:

- `POSTGRES_USER`: PostgreSQL database username
- `POSTGRES_PASSWORD`: PostgreSQL database password
- `POSTGRES_DB`: PostgreSQL database name
- `API_SECRET_KEY`: Secret key for API authentication
- `ENVIRONMENT`: Application environment (development, production)
- `GEMINI_API_KEY`: API key for Google's Gemini AI
- `OPENAI_API_KEY`: API key for OpenAI (fallback AI provider)
- `DEFAULT_LLM_PROVIDER`: Default AI provider for receipt processing

### Next Steps

The FastAPI service is now enabled in the docker-compose.yml file and provides a basic API structure.

### Health Monitoring

The application includes a comprehensive health check system following industry standards:

#### Health Check Endpoints

- **`/health`** or **`/api/v1/health`** - Comprehensive health status of all components
  - Add `?details=true` for detailed component information
  - Returns HTTP 200 (healthy/degraded) or 503 (unhealthy)

- **`/ready`** or **`/api/v1/health/ready`** - Kubernetes readiness probe
  - For load balancers and traffic routing decisions
  - Returns HTTP 200 (ready) or 503 (not ready)

- **`/live`** or **`/api/v1/health/live`** - Kubernetes liveness probe  
  - For container restart decisions
  - Returns HTTP 200 (alive) or 503 (dead)

- **`/api/v1/health/status`** - Simple status check
  - Lightweight endpoint for basic monitoring
  - Always returns HTTP 200 unless completely unresponsive

- **`/ping`** or **`/api/v1/ping`** - Basic connectivity test
  - Simple ping/pong response
  - For basic uptime monitoring

#### Health Check Components

The system monitors:

- **Database**: PostgreSQL connectivity, schema validation, performance
- **Redis Cache**: Cache operations with fallback to in-memory (degraded if unavailable)
- **Configuration**: Required settings, security validations, environment checks
- **LLM Providers**: API key validation for OpenAI/Gemini
- **Storage**: Upload directory permissions, disk space

#### Example Usage

```bash
# Check overall health
curl http://localhost:8000/health

# Get detailed component status
curl http://localhost:8000/health?details=true

# Check if ready for traffic
curl http://localhost:8000/ready

# Basic connectivity test
curl http://localhost:8000/ping
```

For more details, see [Health Check System Documentation](docs/health_check_system.md).

### Running Tests

To run the test suite:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
./run_tests.sh
```

This will run the pytest suite with coverage reporting. Alternatively, you can run pytest directly:

```bash
pytest --cov=app tests/ -v
```
