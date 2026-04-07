# InsightAI - Product Requirements Document

## Overview
InsightAI is an agentic data analytics SaaS platform that allows users to upload CSV datasets, have an AI agent analyze and clean the data in real-time, and generate actionable insights with beautiful visualizations.

## Key Features (Inspired by Competitors)

### From Fabi.ai:
- AI Analyst Agent for 10x exploratory data analysis efficiency
- Natural language querying of datasets
- Self-service analytics environment
- Real-time collaboration features
- Automated workflows with AI data analysis agents
- Multiple data source connections

### From Polymer Search:
- AI-assisted data storytelling
- Beautiful, white-labeled design
- Pre-built reports & self-serve playground
- Secure user access control
- Embedded analytics API

### From Julius AI:
- Chat-based data interaction
- Automatic visualization generation
- Statistical analysis
- Data cleaning automation

## Architecture

### Backend Stack:
- **FastAPI**: High-performance async Python web framework
- **SQLAlchemy**: ORM for PostgreSQL database
- **PostgreSQL**: Primary database for users, datasets, pipelines
- **Celery + Redis**: Async task queue for background processing
- **Docker**: Secure sandbox for code execution
- **OpenAI/Anthropic**: LLM for agentic reasoning

### Frontend Stack:
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Shadcn/ui**: Modern UI components
- **Recharts**: Data visualization
- **Framer Motion**: Smooth animations
- **Zustand**: State management

## Database Schema

### User Model
- id (UUID, PK)
- email (string, unique)
- hashed_password (string)
- full_name (string)
- is_active (boolean)
- is_verified (boolean)
- subscription_tier (enum: free, pro, enterprise)
- created_at, updated_at (timestamps)

### Dataset Model
- id (UUID, PK)
- user_id (FK)
- name (string)
- file_path (string)
- original_filename (string)
- file_size (integer)
- row_count (integer)
- column_count (integer)
- column_schema (JSON)
- status (enum: pending, processing, completed, failed)
- data_health_score (float)
- created_at, updated_at (timestamps)

### CleaningPipeline Model
- id (UUID, PK)
- dataset_id (FK)
- user_id (FK)
- name (string)
- steps (JSON array of cleaning operations)
- is_template (boolean)
- created_at, updated_at (timestamps)

### AnalysisSession Model
- id (UUID, PK)
- dataset_id (FK)
- user_id (FK)
- task_id (string, Celery task ID)
- status (enum: queued, running, completed, failed)
- thought_process (JSON array)
- result_summary (JSON)
- created_at, updated_at (timestamps)

## UI/UX Design Philosophy (Inspired by shed.design & aventuradentalarts.com)

### Visual Style:
- **Dark theme** with subtle gradients
- **Split-screen layouts** like aventuradentalarts.com
- **Large typography** with elegant serif/sans-serif pairings
- **Smooth scroll animations** and transitions
- **Glass morphism** effects for cards and modals
- **Minimalist navigation** with full-screen menu overlay

### Animations:
- Page transitions with fade and slide effects
- Hover states with scale and glow effects
- Terminal typing animation for agent thoughts
- Progress bars with gradient fills
- Staggered card reveals on scroll

### Color Palette:
- Primary: Deep purple (#6D28D9) to blue (#3B82F6) gradient
- Background: Dark slate (#0F172A) to darker (#020617)
- Surface: Slate 800 (#1E293B)
- Accent: Cyan (#06B6D4) and Emerald (#10B981)
- Text: White and Slate 300 (#CBD5E1)

## Pages & Components

### 1. Landing Page
- Hero section with split-screen layout
- Feature showcase with animated cards
- How it works section
- Pricing section
- Testimonials
- CTA section

### 2. Dashboard
- Sidebar navigation with collapsible menu
- Top bar with user profile and notifications
- Dataset cards with preview
- Recent analyses list
- Quick stats (total datasets, analyses, health score)

### 3. Upload Interface
- Drag-and-drop zone with animated border
- File type validation
- Upload progress indicator
- Immediate task creation

### 4. Agent Terminal
- Terminal-like interface showing agent thoughts
- Real-time SSE streaming
- Syntax highlighting for code blocks
- Expandable/collapsible thought steps
- Final result display

### 5. Data Visualization Dashboard
- Summary metrics cards
- Interactive charts (bar, line, pie, scatter)
- Data table with sorting/filtering
- Export options

### 6. Authentication Pages
- Login with email/password
- Signup with verification
- Password reset
- OAuth (Google, GitHub)

## API Endpoints

### Authentication
- POST /auth/register
- POST /auth/login
- POST /auth/logout
- POST /auth/refresh
- POST /auth/forgot-password
- POST /auth/reset-password

### Datasets
- GET /datasets - List user's datasets
- POST /datasets/upload - Upload new dataset
- GET /datasets/{id} - Get dataset details
- DELETE /datasets/{id} - Delete dataset
- GET /datasets/{id}/preview - Get data preview

### Analysis
- POST /analysis/start - Start new analysis
- GET /analysis/{task_id}/status - Get analysis status
- GET /analysis/{task_id}/stream - SSE stream of agent thoughts
- GET /analysis/{task_id}/result - Get final result

### Pipelines
- GET /pipelines - List cleaning pipelines
- POST /pipelines - Create new pipeline
- PUT /pipelines/{id} - Update pipeline
- DELETE /pipelines/{id} - Delete pipeline

## Security Features
- JWT-based authentication
- Password hashing with bcrypt
- Docker sandbox for code execution
- File size and type validation
- Rate limiting
- CORS configuration

## Deployment
- Backend: Docker Compose with FastAPI, PostgreSQL, Redis, Celery Worker
- Frontend: Vercel/Netlify
- File Storage: Local (dev) / S3 (production)
