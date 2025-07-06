# Expense Analyser

## Docker Setup

This project uses Docker Compose to manage its infrastructure. The current setup includes:

- PostgreSQL database service for data storage
- (Upcoming) FastAPI backend service for the application API

### Prerequisites

- Docker and Docker Compose installed on your system
- Copy `.env.app.example` to `.env` and update the values as needed

### Getting Started

1. Clone the repository:

```bash
git clone <repository-url>
cd expense-analyser
```

2. Set up environment variables:

```bash
cp .env.app.example .env
# Edit .env file with your preferred settings and API keys
```

3. Start the Docker containers:

```bash
docker compose up -d
```

4. Verify the database is running:

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
