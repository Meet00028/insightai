"""
# Architect: Meet Kumar
# InsightAI - Celery Tasks
"""

import os
import json
import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.core.celery_config import celery_app
from app.core.database import AsyncSessionLocal
from app.models.dataset import Dataset, DatasetStatus
from app.models.analysis_session import AnalysisSession, AnalysisStatus


class DatabaseTask(Task):
    """Base task class with database session support."""
    
    _db_session = None
    
    async def get_db_session(self):
        """Get async database session."""
        if self._db_session is None:
            self._db_session = AsyncSessionLocal()
        return self._db_session
    
    async def close_db_session(self):
        """Close database session."""
        if self._db_session:
            await self._db_session.close()
            self._db_session = None


@celery_app.task(bind=True, base=DatabaseTask, max_retries=3)
def process_dataset(self, dataset_id: str, file_path: str) -> Dict[str, Any]:
    """
    Process an uploaded dataset file.
    
    Args:
        dataset_id: UUID of the dataset record
        file_path: Path to the uploaded file
    
    Returns:
        Dict with processing results
    """
    self.update_state(state="PROGRESS", meta={"progress": 0, "message": "Starting processing..."})
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Update progress
        self.update_state(state="PROGRESS", meta={"progress": 10, "message": "Loading CSV file..."})
        
        # Load CSV with pandas
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
        
        # Get basic statistics
        row_count = len(df)
        column_count = len(df.columns)
        
        self.update_state(state="PROGRESS", meta={
            "progress": 30, 
            "message": f"Analyzing {row_count} rows and {column_count} columns..."
        })
        
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
        
        self.update_state(state="PROGRESS", meta={"progress": 50, "message": "Calculating data quality metrics..."})
        
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
        
        self.update_state(state="PROGRESS", meta={"progress": 70, "message": "Saving analysis results..."})
        
        # Run async database update
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def update_dataset():
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
        
        loop.run_until_complete(update_dataset())
        loop.close()
        
        self.update_state(state="PROGRESS", meta={"progress": 100, "message": "Processing complete!"})
        
        return {
            "status": "success",
            "dataset_id": dataset_id,
            "row_count": row_count,
            "column_count": column_count,
            "health_score": round(health_score, 2),
            "missing_values": int(missing_values),
            "duplicate_rows": int(duplicate_rows),
        }
        
    except SoftTimeLimitExceeded:
        # Update dataset status to failed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def mark_failed():
            async with AsyncSessionLocal() as session:
                dataset = await session.get(Dataset, dataset_id)
                if dataset:
                    dataset.status = DatasetStatus.FAILED
                    dataset.error_message = "Processing timeout exceeded"
                    await session.commit()
        
        loop.run_until_complete(mark_failed())
        loop.close()
        
        raise
        
    except Exception as exc:
        # Update dataset status to failed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def mark_failed():
            async with AsyncSessionLocal() as session:
                dataset = await session.get(Dataset, dataset_id)
                if dataset:
                    dataset.status = DatasetStatus.FAILED
                    dataset.error_message = str(exc)
                    await session.commit()
        
        loop.run_until_complete(mark_failed())
        loop.close()
        
        # Retry on failure
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        
        raise


@celery_app.task(bind=True, base=DatabaseTask, max_retries=2)
def run_analysis(self, analysis_id: str, dataset_id: str, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Run AI analysis on a dataset.
    
    Args:
        analysis_id: UUID of the analysis session
        dataset_id: UUID of the dataset
        query: Optional natural language query
    
    Returns:
        Dict with analysis results
    """
    from app.services.agent import DataAnalysisAgent
    from app.services.sandbox import DockerSandbox
    
    self.update_state(state="PROGRESS", meta={"progress": 0, "message": "Initializing analysis..."})
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def execute_analysis():
        async with AsyncSessionLocal() as session:
            # Get analysis session and dataset
            analysis = await session.get(AnalysisSession, analysis_id)
            dataset = await session.get(Dataset, dataset_id)
            
            if not analysis or not dataset:
                raise ValueError("Analysis session or dataset not found")
            
            # Update status to running
            analysis.start()
            await session.commit()
            
            try:
                # Initialize agent
                agent = DataAnalysisAgent()
                
                # Get dataset summary
                self.update_state(
                    state="PROGRESS", 
                    meta={"progress": 10, "message": "Loading dataset summary..."}
                )
                
                dataset_summary = {
                    "name": dataset.name,
                    "row_count": dataset.row_count,
                    "column_count": dataset.column_count,
                    "column_schema": dataset.column_schema,
                    "health_score": dataset.data_health_score,
                }
                
                # Generate thought process
                self.update_state(
                    state="PROGRESS", 
                    meta={"progress": 20, "message": "Analyzing data structure..."}
                )
                
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
                self.update_state(
                    state="PROGRESS", 
                    meta={"progress": 30, "message": "Generating analysis plan..."}
                )
                
                plan = await agent.generate_analysis_plan(dataset_summary, query)
                
                analysis.add_thought(
                    "action",
                    f"Analysis plan: {plan['description']}",
                    {"plan_steps": plan["steps"]}
                )
                await session.commit()
                
                # Generate Python code
                self.update_state(
                    state="PROGRESS", 
                    meta={"progress": 50, "message": "Generating analysis code..."}
                )
                
                code = await agent.generate_analysis_code(dataset_summary, plan)
                analysis.generated_code = code
                
                analysis.add_thought(
                    "action",
                    "Generated Python code for analysis.",
                    {"code_preview": code[:500] + "..." if len(code) > 500 else code}
                )
                await session.commit()
                
                # Execute code in sandbox
                self.update_state(
                    state="PROGRESS", 
                    meta={"progress": 70, "message": "Executing analysis in secure sandbox..."}
                )
                
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
                    
                    self.update_state(
                        state="SUCCESS",
                        meta={
                            "progress": 100,
                            "message": "Analysis complete!",
                            "insights_count": len(insights),
                        }
                    )
                    
                else:
                    error_msg = result.get("error", "Unknown error")
                    analysis.add_thought(
                        "error",
                        f"Analysis failed: {error_msg}",
                        {"error": error_msg}
                    )
                    analysis.fail(error_msg)
                    
                    self.update_state(
                        state="FAILURE",
                        meta={"progress": 100, "message": f"Analysis failed: {error_msg}"}
                    )
                
                await session.commit()
                
                return {
                    "status": "success" if result["success"] else "failed",
                    "analysis_id": analysis_id,
                    "insights_count": len(analysis.insights or []),
                }
                
            except Exception as exc:
                analysis.fail(str(exc))
                await session.commit()
                raise
    
    try:
        result = loop.run_until_complete(execute_analysis())
        loop.close()
        return result
        
    except SoftTimeLimitExceeded:
        async def mark_timeout():
            async with AsyncSessionLocal() as session:
                analysis = await session.get(AnalysisSession, analysis_id)
                if analysis:
                    analysis.fail("Analysis timeout exceeded")
                    await session.commit()
        
        loop.run_until_complete(mark_timeout())
        loop.close()
        raise
        
    except Exception as exc:
        loop.close()
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30)
        raise
