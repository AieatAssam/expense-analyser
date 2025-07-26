# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an expense receipt analysis application with a FastAPI backend and React TypeScript frontend. The system processes receipt images using AI (Gemini/OpenAI) to extract expense data and stores it in PostgreSQL.

### Architecture

- **Backend**: FastAPI application (`app/`) with SQLAlchemy ORM and Alembic migrations
- **Frontend**: React TypeScript with Auth0 authentication, Chakra UI, and WebSocket support
- **Database**: PostgreSQL with Alembic migrations
- **AI Processing**: Receipt image processing using Gemini (primary) or OpenAI (fallback)
- **Authentication**: Auth0 integration with multi-account support
- **Deployment**: Docker Compose setup with health checks

## Development Commands

### Backend Development
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest --cov=app tests/ -v

# Run specific test
pytest tests/test_receipt_processing.py -v

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Start backend development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Docker Development
```bash
# Start full stack
docker compose up -d

# View logs
docker compose logs api
docker compose logs db

# Rebuild after changes
docker compose up --build
```

## Key Components

### Backend Core
- `app/core/receipt_processor.py`: Main orchestrator for receipt processing workflow
- `app/core/llm_client.py`: LLM provider abstraction layer (Gemini/OpenAI)
- `app/core/auth.py`: Auth0 JWT authentication
- `app/core/processing_status.py`: Status tracking with WebSocket notifications
- `app/models/receipt.py`: Receipt data model with image storage
- `app/api/endpoints/`: REST API endpoints for receipts, invitations, processing

### Frontend Core
- `frontend/src/contexts/AuthContext.tsx`: Auth0 integration with account switching
- `frontend/src/contexts/ProcessingStatusContext.tsx`: WebSocket status updates
- `frontend/src/components/upload/FileUpload.tsx`: Receipt image upload
- `frontend/src/services/`: API client, WebSocket, user management

### Processing Workflow
1. Receipt uploaded → stored in database with image data
2. `ReceiptProcessingOrchestrator` initiates processing
3. LLM extracts structured data from image
4. Data validated and stored as line items/categories
5. Status updates sent via WebSocket
6. Results available through API

## Database Schema

- `User`: Auth0 users with multi-account support
- `Account`: Business accounts for expense organization
- `Receipt`: Receipt metadata with embedded image data
- `LineItem`: Individual expense items from receipts
- `Category`: Expense categorization
- `ProcessingEvent`: Status tracking and audit trail

## Environment Variables

Required variables (see `.env.app.example`):
- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: Google Gemini API key
- `OPENAI_API_KEY`: OpenAI API key (fallback)
- `DEFAULT_LLM_PROVIDER`: "gemini" or "openai"
- `API_SECRET_KEY`: JWT signing key

## Testing

- Backend: pytest with coverage reporting and Docker container tests
- Frontend: Jest with React Testing Library
- Integration: Container-based end-to-end tests
- Test data available in `tests/testdata/`

## Migration Management

Use Alembic for database schema changes:
- Auto-generate: `alembic revision --autogenerate -m "description"`
- Apply: `alembic upgrade head`
- Migration files in `migrations/versions/`