# InsightAI: Autonomous Agentic Data Platform

![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=for-the-badge&logo=postgresql)
![LangChain](https://img.shields.io/badge/LangChain-Agentic-1C3C3C?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-LPU_Inference-F55036?style=for-the-badge)

InsightAI is an enterprise-grade, split-brain web application that transforms static datasets into interactive insights. By coupling a high-performance Next.js frontend with an asynchronous Python/FastAPI backend, it deploys a LangChain-powered ReAct agent capable of dynamically writing and executing Python code to analyze user data in real-time.

## System Architecture

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
