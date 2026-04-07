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

        # Create the agent
        # Note: allow_dangerous_code=True is required for pandas agent to execute python code
        agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=True,
            agent_type="tool-calling",
            allow_dangerous_code=True,
            prefix=(
                "You are an elite Autonomous Data Analyst. "
                "If the user asks a question that requires data cleaning (e.g., converting a string column to datetime, handling missing values, or dropping rows), "
                "YOU HAVE PERMISSION TO WRITE AND EXECUTE THE PANDAS CODE TO FIX THE DATAFRAME IN MEMORY before answering. "
                "Always convert date columns to proper datetime objects before doing time-series analysis.\n\n"
                "If the user explicitly asks to visualize data, plot a chart, or show a trend, YOU MUST NOT just explain it. "
                "You must extract the relevant data from the dataframe and output a JSON code block. "
                "The JSON MUST follow this exact structure:\n"
                "```json\n"
                "{\n"
                '  "is_chart_data": true,\n'
                '  "type": "bar", // or "line" or "pie"\n'
                '  "title": "A descriptive title",\n'
                '  "xAxis": "column_name_for_x",\n'
                '  "yAxis": "column_name_for_y",\n'
                '  "data": [{"column_name_for_x": "Label", "column_name_for_y": 123}, ...]\n'
                "}\n"
                "```\n"
                "The 'data' array MUST contain the actual calculated values from the dataframe. "
                "Do not include any other markdown code blocks in that specific response, just the JSON block and a brief text explanation above it.\n\n"
                "If the user asks to export, download, or save the cleaned data, YOU MUST write the current state of the pandas dataframe to a file named "
                f"'{settings.UPLOAD_DIR}/{request.session_id}_cleaned.csv'. After successfully saving it, output a JSON code block exactly like this:\n"
                "```json\n"
                "{\n"
                '  "is_export": true,\n'
                '  "message": "Your cleaned dataset is ready for download."\n'
                "}\n"
                "```\n"
                "Do not output any other text or markdown when exporting."
            )
        )

        # 4. Prepare the prompt with history if available
        full_query = ""
        if request.history:
            history_str = "\n".join([f"{h.role}: {h.content}" for h in request.history])
            full_query = f"Previous conversation:\n{history_str}\n\nUser: {request.message}"
        else:
            full_query = request.message

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
