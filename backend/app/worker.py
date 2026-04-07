import os
import json
import re
import time
import asyncio
from typing import Any, Dict
from sqlalchemy import update, create_engine, select
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from celery import Celery
from celery.schedules import crontab
import pandas as pd
from langchain_groq import ChatGroq

load_dotenv(override=True)

async def update_session_in_db(session_id: str, metadata: dict, ai_json: dict): 
    from app.core.database import AsyncSessionLocal 
    from app.models.analysis_session import AnalysisSession, AnalysisStatus 
     
    async with AsyncSessionLocal() as db: 
        # Async query to get the session 
        result = await db.execute(select(AnalysisSession).where(AnalysisSession.id == session_id)) 
        db_session = result.scalar_one_or_none() 
         
        if db_session: 
            db_session.status = AnalysisStatus.COMPLETED 
            db_session.result_summary = {"metadata": metadata, "ai_insights": ai_json} 
            await db.commit() 
            print(f"SUCCESS: Database async updated for session {session_id}") 

# Create a synchronous engine for the worker to avoid async issues
# We replace postgresql+asyncpg:// with postgresql:// for sync operations
database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/insightai")
sync_database_url = database_url.replace("asyncpg", "psycopg2") if "asyncpg" in database_url else database_url
sync_engine = create_engine(sync_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

celery_app = Celery(
    "insightai",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL"),
)

app = celery_app

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    beat_schedule={
        "cleanup-old-files-every-hour": {
            "task": "cleanup_old_files",
            "schedule": 3600.0,  # Every hour
        },
    },
)

def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and "text" in part and isinstance(part["text"], str):
                parts.append(part["text"])
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content)

def _parse_first_json_object(text: str) -> Dict[str, Any]:
    # 1. Strip and basic cleanup
    cleaned = text.strip()
    cleaned = re.sub(r"^\s*```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)

    # 2. Sanitize: remove or replace invalid control characters (0x00-0x1F) except \n, \r, \t
    # These often cause JSONDecodeError: Invalid control character
    sanitized = "".join(ch if ord(ch) >= 32 or ch in "\n\r\t" else " " for ch in cleaned)

    try:
        return json.loads(sanitized, strict=False)
    except Exception:
        # Fallback: extract the outermost { ... }
        start = sanitized.find("{")
        end = sanitized.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(sanitized[start : end + 1], strict=False)
            except Exception:
                # If that still fails, try a more aggressive approach or re-raise
                pass
        raise

@celery_app.task(bind=True, name="process_data_task")
def process_data_task(self, file_path: str, prompt: str, session_id: str) -> Dict[str, Any]:
    self.update_state(state="PROGRESS", meta={"message": "Loading CSV"})

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_csv(file_path)

    metadata = {
        "column_names": df.columns.tolist(),
        "data_types": df.dtypes.apply(lambda x: str(x)).to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "statistical_summary": json.loads(df.describe(include="all").to_json()),
        "row_count": len(df),
        "column_count": len(df.columns),
    }

    df_head = json.loads(df.head(5).to_json())

    final_prompt = prompt.format(metadata=json.dumps(metadata), df_head=json.dumps(df_head))
    final_prompt += "\n\nYou MUST return your entire response as a single, perfectly formatted JSON object."

    self.update_state(state="PROGRESS", meta={"message": "Calling LLM"})

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in the environment.")

    model = ChatGroq(model="llama-3.1-8b-instant", api_key=api_key, model_kwargs={"response_format": {"type": "json_object"}})
    
    # Try multiple times to get a valid JSON from LLM
    max_retries = 3
    ai_content = ""
    ai_json = None
    last_error = None

    for i in range(max_retries):
        try:
            response = model.invoke(final_prompt)
            ai_content = _extract_text_content(response.content)
            ai_json = _parse_first_json_object(ai_content)
            if ai_json:
                break
        except Exception as e:
            last_error = e
            print(f"Retry {i+1} due to: {e}")
            continue

    if not ai_json:
        raise last_error if last_error else RuntimeError("Failed to parse LLM response after retries.")

    asyncio.run(update_session_in_db(session_id, metadata, ai_json))

    return {
        "metadata": metadata,
        "ai_insights": ai_json,
    }

@celery_app.task(name="cleanup_old_files")
def cleanup_old_files():
    """
    Delete files in UPLOAD_DIR that are older than 24 hours.
    """
    upload_dir = os.getenv("UPLOAD_DIR", "temp_data")
    if not os.path.exists(upload_dir):
        print(f"Cleanup: Directory {upload_dir} does not exist.")
        return {"status": "error", "message": "Directory not found"}

    now = time.time()
    retention_period = 24 * 3600  # 24 hours in seconds
    
    files_deleted = 0
    errors = 0

    try:
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            
            # Skip directories
            if not os.path.isfile(file_path):
                continue

            try:
                file_mtime = os.path.getmtime(file_path)
                if now - file_mtime > retention_period:
                    os.remove(file_path)
                    files_deleted += 1
                    print(f"Deleted old file: {filename}")
            except Exception as e:
                print(f"Cleanup error for {filename}: {e}")
                errors += 1
    except Exception as e:
        print(f"Cleanup task failed: {e}")
        return {"status": "failed", "error": str(e)}

    print(f"Cleanup completed: {files_deleted} files deleted, {errors} errors encountered.")
    return {"status": "success", "deleted": files_deleted, "errors": errors}
