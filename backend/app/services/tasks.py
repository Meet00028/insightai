"""
# Architect: Meet Kumar
# InsightAI - Background Tasks
"""

import os
import json
import logging
import re
import time
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from langchain_groq import ChatGroq

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.dataset import Dataset, DatasetStatus
from app.models.analysis_session import AnalysisSession, AnalysisStatus

logger = logging.getLogger(__name__)

def _extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
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
                pass
        raise

async def process_data_task(file_path: str, prompt: str, session_id: str) -> Dict[str, Any]:
    """
    Process data using LLM in the background.
    """
    logger.info(f"Starting process_data_task for session {session_id}")
    
    try:
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

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set in the environment.")

        model = ChatGroq(model="llama-3.1-8b-instant", api_key=api_key, model_kwargs={"response_format": {"type": "json_object"}})
        
        # Try multiple times to get a valid JSON from LLM
        max_retries = 3
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
                logger.warning(f"Retry {i+1} for session {session_id} due to: {e}")
                continue

        if not ai_json:
            raise last_error if last_error else RuntimeError("Failed to parse LLM response after retries.")

        # Update session in DB with fresh session
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AnalysisSession).where(AnalysisSession.id == session_id))
            db_session = result.scalar_one_or_none()
            
            if db_session:
                db_session.status = AnalysisStatus.COMPLETED
                db_session.result_summary = {"metadata": metadata, "ai_insights": ai_json}
                db_session.completed_at = datetime.utcnow()
                await db.commit()
                logger.info(f"SUCCESS: Database updated for session {session_id}")

        return {
            "metadata": metadata,
            "ai_insights": ai_json,
        }
    except Exception as e:
        logger.error(f"Error in process_data_task for session {session_id}: {str(e)}")
        # Guaranteed update to failed on error
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(AnalysisSession).where(AnalysisSession.id == session_id))
                db_session = result.scalar_one_or_none()
                if db_session:
                    db_session.status = AnalysisStatus.FAILED
                    db_session.error_message = str(e)
                    await db.commit()
                    logger.info(f"FAILED: Database updated for session {session_id}")
        except Exception as db_err:
            logger.error(f"Critical error updating database for failed session {session_id}: {str(db_err)}")
            
        return {"status": "failed", "error": str(e)}

async def cleanup_old_files():
    """
    Delete files in UPLOAD_DIR that are older than 24 hours.
    """
    upload_dir = os.getenv("UPLOAD_DIR", "temp_data")
    if not os.path.exists(upload_dir):
        logger.warning(f"Cleanup: Directory {upload_dir} does not exist.")
        return {"status": "error", "message": "Directory not found"}

    now = time.time()
    retention_period = 24 * 3600  # 24 hours in seconds
    
    files_deleted = 0
    errors = 0

    try:
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            
            if not os.path.isfile(file_path):
                continue

            try:
                file_mtime = os.path.getmtime(file_path)
                if now - file_mtime > retention_period:
                    os.remove(file_path)
                    files_deleted += 1
                    logger.info(f"Deleted old file: {filename}")
            except Exception as e:
                logger.error(f"Cleanup error for {filename}: {e}")
                errors += 1
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {"status": "failed", "error": str(e)}

    logger.info(f"Cleanup completed: {files_deleted} files deleted, {errors} errors encountered.")
    return {"status": "success", "deleted": files_deleted, "errors": errors}

async def process_dataset(dataset_id: str, file_path: str) -> Dict[str, Any]:
    """
    Process an uploaded dataset file in the background.
    
    Args:
        dataset_id: UUID of the dataset record
        file_path: Path to the uploaded file
    
    Returns:
        Dict with processing results
    """
    logger.info(f"Starting background processing for dataset {dataset_id}")
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load CSV with pandas
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
        
        # Get basic statistics
        row_count = len(df)
        column_count = len(df.columns)
        
        # Build column schema
        column_schema = {}
        for col in df.columns:
            col_data = df[col]
            column_schema[col] = {
                "dtype": str(col_data.dtype),
                "nullable": col_data.isna().any(),
                "null_count": int(col_data.isna().sum()),
                "unique_values": int(col_data.nunique()),
                "sample_values": col_data.dropna().head(5).tolist(),
            }
            
            # Add type-specific stats
            if pd.api.types.is_numeric_dtype(col_data):
                column_schema[col].update({
                    "min": float(col_data.min()) if not col_data.isna().all() else None,
                    "max": float(col_data.max()) if not col_data.isna().all() else None,
                    "mean": float(col_data.mean()) if not col_data.isna().all() else None,
                })
        
        # Calculate data quality metrics
        total_cells = row_count * column_count
        missing_values = df.isna().sum().sum()
        missing_percentage = (missing_values / total_cells) * 100 if total_cells > 0 else 0
        
        # Count duplicate rows
        duplicate_rows = df.duplicated().sum()
        
        # Calculate health score (0-100)
        # Higher is better; penalizes missing values and duplicates
        health_score = 100
        health_score -= missing_percentage * 0.5  # Deduct 0.5 per % of missing values
        health_score -= (duplicate_rows / max(row_count, 1)) * 10  # Deduct up to 10 for duplicates
        health_score = max(0, min(100, health_score))
        
        # Update dataset in database with fresh session
        async with AsyncSessionLocal() as session:
            dataset = await session.get(Dataset, dataset_id)
            if dataset:
                dataset.row_count = row_count
                dataset.column_count = column_count
                dataset.column_schema = column_schema
                dataset.status = DatasetStatus.COMPLETED
                dataset.data_health_score = round(health_score, 2)
                dataset.missing_values_count = int(missing_values)
                dataset.duplicate_rows_count = int(duplicate_rows)
                dataset.processed_at = datetime.utcnow()
                await session.commit()
        
        logger.info(f"Processing complete for dataset {dataset_id}")
        
        return {
            "status": "success",
            "dataset_id": dataset_id,
            "row_count": row_count,
            "column_count": column_count,
            "health_score": round(health_score, 2),
            "missing_values": int(missing_values),
            "duplicate_rows": int(duplicate_rows),
        }
        
    except Exception as exc:
        logger.error(f"Error processing dataset {dataset_id}: {str(exc)}")
        # Guaranteed update to failed on error
        try:
            async with AsyncSessionLocal() as session:
                dataset = await session.get(Dataset, dataset_id)
                if dataset:
                    dataset.status = DatasetStatus.FAILED
                    dataset.error_message = str(exc)
                    await session.commit()
                    logger.info(f"FAILED: Database updated for dataset {dataset_id}")
        except Exception as db_err:
            logger.error(f"Critical error updating database for failed dataset {dataset_id}: {str(db_err)}")
            
        return {
            "status": "failed",
            "dataset_id": dataset_id,
            "error": str(exc)
        }


async def run_analysis(analysis_id: str, dataset_id: str, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Run AI analysis on a dataset in the background.
    
    Args:
        analysis_id: UUID of the analysis session
        dataset_id: UUID of the dataset
        query: Optional natural language query
    
    Returns:
        Dict with analysis results
    """
    from app.services.agent import DataAnalysisAgent
    from app.services.sandbox import DockerSandbox
    
    logger.info(f"Starting background analysis {analysis_id} for dataset {dataset_id}")
    
    try:
        async with AsyncSessionLocal() as session:
            # Get analysis session and dataset
            analysis = await session.get(AnalysisSession, analysis_id)
            dataset = await session.get(Dataset, dataset_id)
            
            if not analysis or not dataset:
                logger.error(f"Analysis {analysis_id} or dataset {dataset_id} not found")
                return {"status": "failed", "error": "Analysis session or dataset not found"}
            
            # Update status to running
            analysis.start()
            await session.commit()
            
            try:
                # Initialize agent
                agent = DataAnalysisAgent()
                
                dataset_summary = {
                    "name": dataset.name,
                    "row_count": dataset.row_count,
                    "column_count": dataset.column_count,
                    "column_schema": dataset.column_schema,
                    "health_score": dataset.data_health_score,
                }
                
                # Generate thought process
                analysis.add_thought(
                    "thinking",
                    f"Starting analysis of dataset '{dataset.name}' with {dataset.row_count} rows and {dataset.column_count} columns.",
                    {"dataset_summary": dataset_summary}
                )
                await session.commit()
                
                # Determine analysis approach based on query
                if query:
                    analysis.add_thought(
                        "thinking",
                        f"User query: '{query}'. Interpreting intent and planning analysis steps.",
                        {"query": query}
                    )
                    await session.commit()
                
                # Generate analysis plan
                plan = await agent.generate_analysis_plan(dataset_summary, query)
                
                analysis.add_thought(
                    "action",
                    f"Analysis plan: {plan['description']}",
                    {"plan_steps": plan["steps"]}
                )
                await session.commit()
                
                # Generate Python code
                code = await agent.generate_analysis_code(dataset_summary, plan)
                analysis.generated_code = code
                
                analysis.add_thought(
                    "action",
                    "Generated Python code for analysis.",
                    {"code_preview": code[:500] + "..." if len(code) > 500 else code}
                )
                await session.commit()
                
                # Execute code in sandbox
                sandbox = DockerSandbox()
                result = await sandbox.execute_python_script(
                    script=code,
                    csv_path=dataset.file_path,
                    timeout=300
                )
                
                if result["success"]:
                    analysis.add_thought(
                        "result",
                        "Analysis completed successfully.",
                        {"output": result["output"][:1000] if len(result["output"]) > 1000 else result["output"]}
                    )
                    
                    # Parse insights from output
                    insights = agent.parse_insights(result["output"])
                    analysis.insights = insights
                    
                    # Complete analysis
                    analysis.complete({
                        "output": result["output"],
                        "insights_count": len(insights),
                        "execution_time": result.get("execution_time"),
                    })
                    
                else:
                    error_msg = result.get("error", "Unknown error")
                    analysis.add_thought(
                        "error",
                        f"Analysis failed: {error_msg}",
                        {"error": error_msg}
                    )
                    analysis.fail(error_msg)
                
                await session.commit()
                logger.info(f"Analysis {analysis_id} completed with status: {'success' if result['success'] else 'failed'}")
                
                return {
                    "status": "success" if result["success"] else "failed",
                    "analysis_id": analysis_id,
                    "insights_count": len(analysis.insights or []),
                }
                
            except Exception as exc:
                logger.error(f"Error in analysis {analysis_id}: {str(exc)}")
                analysis.fail(str(exc))
                await session.commit()
                return {"status": "failed", "error": str(exc)}
                
    except Exception as outer_exc:
        logger.error(f"Outer error in analysis {analysis_id}: {str(outer_exc)}")
        # Guaranteed update to failed on error
        try:
            async with AsyncSessionLocal() as session:
                analysis = await session.get(AnalysisSession, analysis_id)
                if analysis:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.error_message = str(outer_exc)
                    await session.commit()
                    logger.info(f"FAILED (outer): Database updated for analysis {analysis_id}")
        except Exception as db_err:
            logger.error(f"Critical error updating database for failed analysis {analysis_id}: {str(db_err)}")
            
        return {"status": "failed", "error": str(outer_exc)}
