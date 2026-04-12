# 🧠 InsightAI: Autonomous Agentic Data Platform

![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=for-the-badge&logo=postgresql)
![LangChain](https://img.shields.io/badge/LangChain-Agentic-1C3C3C?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-LPU_Inference-F55036?style=for-the-badge)

InsightAI is an enterprise-grade, split-brain web application that transforms static datasets into interactive insights. By coupling a high-performance Next.js frontend with an asynchronous Python/FastAPI backend, it deploys a LangChain-powered ReAct agent capable of dynamically writing and executing Python code to analyze user data in real-time.

## 🏗️ System Architecture

InsightAI operates on a decoupled microservices architecture, sharing a highly synchronized, single-source-of-truth PostgreSQL database.

```mermaid
graph TD
    Client[Next.js Frontend] -->|JWT / NextAuth| Auth[Google SSO & Credentials]
    Client -->|REST API| Server[FastAPI Backend]
    
    subgraph Neon Serverless PostgreSQL
        DB[(Unified Database)]
    end
    
    Auth -->|Prisma ORM| DB
    Server -->|SQLAlchemy| DB
    
    Server -->|Prompt/Context| LangChain[LangChain ReAct Agent]
    LangChain -->|LPU Inference| Groq[Groq API]
    LangChain -->|AST Execution| Pandas[Pandas DataFrame]

Core Engineering Features
1. Autonomous Agentic Analysis
Instead of relying on pre-computed SQL queries, the backend utilizes a LangChain AgentExecutor paired with the Groq LPU API. When a user queries a dataset, the agent securely generates, evaluates, and executes an Abstract Syntax Tree (AST) Python script using pandas, returning mathematical insights and JSON chart schemas in milliseconds.

2. Unified Split-Brain Database
A major architectural challenge was maintaining schema integrity between two distinct ORMs: Prisma (Next.js/NextAuth) and SQLAlchemy (FastAPI).

Engineered a master schema.prisma mapping that cleanly integrates NextAuth's OAuth tables (Account, Session) alongside FastAPI's custom PostgreSQL Enums (subscriptiontier, datasetstatus) and hashed_password columns.

This ensures zero data corruption or column drops between the Python processing engine and the JavaScript authentication layer.

3. Asynchronous Data Pipelines
The FastAPI backend is entirely async, capable of parsing massive CSV uploads, generating data health scores (missing values, duplicate rows), and pushing the clean data into isolated temporary storage without blocking the event loop.

Quick Start
Prerequisites
Node.js 18+

Python 3.10+

A Neon PostgreSQL Database URL

A Groq API Key

Backend Setup (FastAPI)
Bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Add .env with DATABASE_URL and GROQ_API_KEY
uvicorn main:app --reload --port 8000
Frontend Setup (Next.js)
Bash
cd frontend
npm install
# Add .env with NEXTAUTH_SECRET, GOOGLE_CLIENT_ID, etc.
npx prisma generate
npx prisma db push
npm run dev
Security & Authentication
Secured via NextAuth.js, supporting both classic encrypted credentials (bcrypt) and Google OAuth 2.0. Sessions are managed seamlessly across the frontend application while FastAPI validates user UUIDs for all sensitive data processing endpoints.
