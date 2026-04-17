"""
# Architect: Meet Kumar
# InsightAI - Chat Endpoint
"""

import os
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db
from app.core.config import settings
from app.models.dataset import Dataset
from app.api.schemas import ChatRequest, ChatResponse
from langchain_groq import ChatGroq
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_dataset(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with a dataset using session_id (dataset_id).
    """
    try:
        # 1. First check if it's a real dataset in the DB
        dataset = None
        try:
            dataset_uuid = UUID(request.session_id)
            result = await db.execute(
                select(Dataset).where(Dataset.id == dataset_uuid)
            )
            dataset = result.scalar_one_or_none()
        except ValueError:
            pass # Not a UUID, check filesystem next

        # 2. Reconstruct path if not found in DB (fallback for demo uploads)
        if dataset:
            file_path = dataset.file_path
        else:
            # Check temp_data directory for {session_id}.csv
            file_path = os.path.join(settings.UPLOAD_DIR, f"{request.session_id}.csv")

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset file not found on server."
            )

        # 2. Load the dataset
        df = pd.read_csv(file_path)

        # 3. Initialize LangChain Pandas Agent
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Groq API key not configured."
            )

        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=api_key,
            temperature=0
        )

        agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=True,
            agent_type="tool-calling",
            allow_dangerous_code=True,
            prefix=(
                "You are InsightAI, an elite data scientist and Python expert. "
                "You have access to a pandas DataFrame. Write safe, efficient Pandas code to answer the user's question.\n\n"
                "RULES:\n"
                "1. NEVER read or print the entire dataset into text. Use only the columns provided in the context.\n"
                "2. Return exact numerical insights when calculating statistics.\n"
                "3. Keep reasoning concise, mathematical, and highly accurate.\n\n"
                "CHART FORMATTING: If the user asks to visualize data or show trends, output a JSON code block:\n"
                "```json\n"
                "{\n"
                '  "is_chart_data": true,\n'
                '  "type": "bar",\n'
                '  "title": "Descriptive title",\n'
                '  "xAxis": "column_name",\n'
                '  "yAxis": "column_name",\n'
                '  "data": [{"x": "label", "y": 123}, ...]\n'
                "}\n"
                "```\n\n"
                "EXPORT FORMATTING: If the user asks to export/download/save cleaned data, write the dataframe to "
                f"'{settings.UPLOAD_DIR}/{request.session_id}_cleaned.csv' and output:\n"
                "```json\n"
                "{\n"
                '  "is_export": true,\n'
                '  "message": "Your cleaned dataset is ready for download."\n'
                "}\n"
                "```"
            )
        )

        # 3. Extract lightweight metadata to avoid token limit errors
        column_names = df.columns.tolist()
        data_types = df.dtypes.astype(str).to_dict()
        sample_data = df.head(3).to_markdown()

        # 4. Build the Clean Enterprise Prompt
        full_query = f"""
CRITICAL DATA CONTEXT:
- Columns available: {column_names}
- Data types: {data_types}
- Sample Data (first 3 rows):
{sample_data}

USER QUESTION:
"{request.message}"

Please analyze this using the columns provided. Do not read the entire dataset into text.
"""

        # 5. Execute the query
        response = await agent.ainvoke({"input": full_query})
        
        reply = response.get("output", "I'm sorry, I couldn't process that request.")

        return ChatResponse(reply=reply)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during chat: {str(e)}"
        )
