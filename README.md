# InsightAI - AI-Powered Data Analytics Platform

InsightAI is a comprehensive agentic data analytics SaaS platform that allows users to upload CSV datasets, have an AI agent analyze and clean the data in real-time, and generate actionable insights with beautiful visualizations.

## Features

- **AI-Powered Analysis**: Let our intelligent agent analyze your data, identify patterns, and generate insights automatically
- **Real-time Processing**: Watch the AI think in real-time with our streaming terminal interface
- **Secure Sandbox**: All code execution happens in isolated Docker containers
- **Beautiful Visualizations**: Generate stunning charts and graphs automatically
- **Data Cleaning**: Automatically detect and fix data quality issues
- **Natural Language**: Ask questions about your data in plain English

## Architecture

### Backend Stack
- **FastAPI**: High-performance async Python web framework
- **SQLAlchemy**: ORM for PostgreSQL database
- **PostgreSQL**: Primary database
- **Celery + Redis**: Async task queue
- **Docker**: Secure sandbox for code execution
- **OpenAI/Anthropic**: LLM for agentic reasoning

### Frontend Stack
- **React + TypeScript**: Modern frontend framework
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Smooth animations
- **Zustand**: State management
- **TanStack Query**: Data fetching
- **Recharts**: Data visualization

## Project Structure

```
insightai/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Config, security, database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic, AI agent, sandbox
│   │   └── main.py         # FastAPI app entry
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   ├── store/          # Zustand stores
│   │   ├── api/            # API client
│   │   └── types/          # TypeScript types
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a `.env` file:
```bash
cp .env.example .env
```

3. Update the `.env` file with your configuration:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/insightai
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

4. Start the services with Docker Compose:
```bash
docker-compose up -d
```

5. The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file:
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

4. Start the development server:
```bash
npm run dev
```

5. The frontend will be available at `http://localhost:3000`

## API Documentation

Once the backend is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Key Features

### Authentication
- JWT-based authentication
- Email/password login
- Token refresh
- Protected routes

### Datasets
- CSV file upload
- Automatic data profiling
- Health score calculation
- Data preview

### AI Analysis
- Natural language queries
- Real-time thought streaming via SSE
- Docker sandbox execution
- Automatic visualization generation

### Cleaning Pipelines
- Reusable cleaning workflows
- Template sharing
- Step-by-step operations

## Environment Variables

### Backend
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `SECRET_KEY` | JWT secret key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `UPLOAD_DIR` | File upload directory | `temp_data` |
| `MAX_FILE_SIZE` | Max upload size in bytes | `104857600` |

### Frontend
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | - |

## Development

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm test
```

### Code Quality

Backend:
```bash
black app/
isort app/
flake8 app/
```

Frontend:
```bash
npm run lint
```

## Deployment

### Docker Deployment

1. Build and start all services:
```bash
docker-compose up -d --build
```

2. Scale Celery workers:
```bash
docker-compose up -d --scale celery-worker=4
```

### Production Considerations

- Use a production-grade PostgreSQL instance
- Set up Redis with persistence
- Configure proper CORS origins
- Use HTTPS for all communications
- Set up monitoring and logging
- Configure backup strategies

## License

MIT License - see LICENSE file for details

## Author

**Meet Kumar** - Architect & Lead Developer
