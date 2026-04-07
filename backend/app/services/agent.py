"""
# Architect: Meet Kumar
# InsightAI - AI Agent for Data Analysis
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_groq import ChatGroq

from app.core.config import settings


class DataAnalysisAgent:
    """
    AI Agent for automated data analysis.
    
    This agent uses LLM to:
    1. Analyze dataset structure and quality
    2. Generate analysis plans
    3. Create Python code for data processing
    4. Interpret results and extract insights
    """
    
    def __init__(self, provider: str = "groq"):
        self.provider = provider
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize LLM client."""
        if self.provider == "groq":
            if os.environ.get("GROQ_API_KEY"):
                self.client = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    api_key=os.environ.get("GROQ_API_KEY"),
                    temperature=0.7
                )
            else:
                raise RuntimeError("GROQ_API_KEY not found in environment")
        elif self.provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            if os.environ.get("GEMINI_API_KEY"):
                self.client = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    api_key=os.environ.get("GEMINI_API_KEY"),
                    temperature=0.7
                )
            else:
                raise RuntimeError("GEMINI_API_KEY not found in settings")
        elif self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError:
                raise RuntimeError("OpenAI package not installed")
        elif self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            except ImportError:
                raise RuntimeError("Anthropic package not installed")
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    async def generate_analysis_plan(
        self,
        dataset_summary: Dict[str, Any],
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an analysis plan based on dataset and optional user query.
        
        Args:
            dataset_summary: Dict with dataset info (columns, types, etc.)
            query: Optional natural language query from user
        
        Returns:
            Dict with analysis plan
        """
        columns_info = dataset_summary.get("column_schema", {})
        row_count = dataset_summary.get("row_count", 0)
        health_score = dataset_summary.get("health_score", 100)
        
        # Build prompt
        prompt = f"""You are an expert data analyst. Given the following dataset information, create a detailed analysis plan.

Dataset Summary:
- Name: {dataset_summary.get('name', 'Unknown')}
- Rows: {row_count}
- Columns: {dataset_summary.get('column_count', 0)}
- Health Score: {health_score}/100

Column Information:
"""
        
        for col_name, col_info in columns_info.items():
            prompt += f"\n- {col_name} ({col_info.get('dtype', 'unknown')}): "
            prompt += f"{col_info.get('null_count', 0)} nulls, "
            prompt += f"{col_info.get('unique_values', 0)} unique values"
            if 'min' in col_info:
                prompt += f", range: {col_info['min']:.2f} to {col_info['max']:.2f}"
        
        if query:
            prompt += f"\n\nUser Query: {query}"
        
        prompt += """

Create an analysis plan with the following structure:
{
    "description": "Brief description of the analysis approach",
    "steps": [
        {"order": 1, "action": "Load and validate data", "details": "..."},
        {"order": 2, "action": "Data cleaning", "details": "..."},
        {"order": 3, "action": "Exploratory analysis", "details": "..."},
        ...
    ],
    "expected_outputs": ["summary_stats", "visualizations", "insights"]
}

Respond with ONLY the JSON object, no markdown formatting."""
        
        # Call LLM
        response = await self._call_llm(prompt, temperature=0.3)
        
        try:
            # Extract JSON from response
            plan = self._extract_json(response)
            return plan
        except Exception as e:
            # Return default plan if parsing fails
            return {
                "description": "Standard exploratory data analysis",
                "steps": [
                    {"order": 1, "action": "Load data", "details": "Load CSV and validate structure"},
                    {"order": 2, "action": "Basic statistics", "details": "Calculate summary statistics"},
                    {"order": 3, "action": "Missing values analysis", "details": "Identify and report missing values"},
                    {"order": 4, "action": "Correlation analysis", "details": "Analyze correlations between numeric columns"},
                ],
                "expected_outputs": ["summary_stats", "correlation_matrix"]
            }
    
    async def generate_analysis_code(
        self,
        dataset_summary: Dict[str, Any],
        plan: Dict[str, Any]
    ) -> str:
        """
        Generate Python code for the analysis plan.
        
        Args:
            dataset_summary: Dataset information
            plan: Analysis plan from generate_analysis_plan
        
        Returns:
            Python code as string
        """
        columns = list(dataset_summary.get("column_schema", {}).keys())
        numeric_cols = [
            col for col, info in dataset_summary.get("column_schema", {}).items()
            if "int" in info.get("dtype", "").lower() or "float" in info.get("dtype", "").lower()
        ]
        
        prompt = f"""You are an expert Python data analyst. Write a complete Python script for data analysis.

The script will:
1. Read a CSV file from '/data/input.csv'
2. Perform the following analysis:
"""
        
        for step in plan.get("steps", []):
            prompt += f"\n- {step.get('order')}. {step.get('action')}: {step.get('details', '')}"
        
        prompt += f"""

Dataset Info:
- Columns: {columns}
- Numeric columns: {numeric_cols}
- Rows: {dataset_summary.get('row_count', 0)}

Requirements:
1. Use pandas for data manipulation
2. Print clear, formatted output
3. Include error handling
4. Output results in a structured format
5. Generate insights about the data

Write the complete Python script. The script should:
- Read the CSV from '/data/input.csv'
- Print analysis results to stdout
- Use JSON format for structured outputs where appropriate
- Include comments explaining each step

Respond with ONLY the Python code, no markdown formatting or explanations."""
        
        code = await self._call_llm(prompt, temperature=0.2)
        
        # Clean up code (remove markdown code blocks if present)
        code = self._clean_code(code)
        
        return code
    
    async def generate_cleaning_code(
        self,
        dataset_summary: Dict[str, Any],
        steps: List[Dict[str, Any]]
    ) -> str:
        """
        Generate Python code for data cleaning operations.
        
        Args:
            dataset_summary: Dataset information
            steps: List of cleaning steps
        
        Returns:
            Python code as string
        """
        prompt = f"""Write a Python script to clean a dataset based on the following steps.

Dataset Info:
- Columns: {list(dataset_summary.get('column_schema', {}).keys())}
- Rows: {dataset_summary.get('row_count', 0)}

Cleaning Steps:
"""
        for step in steps:
            prompt += f"\n- {step.get('operation')}: {step.get('params', {})}"
        
        prompt += """

The script should:
1. Read CSV from '/data/input.csv'
2. Apply each cleaning step
3. Save cleaned data to '/app/outputs/cleaned_data.csv'
4. Print a summary of changes made
5. Return cleaning statistics as JSON

Respond with ONLY the Python code."""
        
        code = await self._call_llm(prompt, temperature=0.2)
        return self._clean_code(code)
    
    def parse_insights(self, output: str) -> List[Dict[str, Any]]:
        """
        Parse insights from analysis output.
        
        Args:
            output: Raw output from script execution
        
        Returns:
            List of insight dictionaries
        """
        insights = []
        
        # Try to extract JSON sections
        json_pattern = r'```json\s*(.*?)\s*```'
        json_matches = re.findall(json_pattern, output, re.DOTALL)
        
        for match in json_matches:
            try:
                data = json.loads(match)
                if isinstance(data, list):
                    insights.extend(data)
                elif isinstance(data, dict):
                    insights.append(data)
            except json.JSONDecodeError:
                continue
        
        # If no JSON found, extract key findings from text
        if not insights:
            lines = output.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('import'):
                    if any(keyword in line.lower() for keyword in ['found', 'discovered', 'identified', 'observed', 'significant', 'correlation', 'trend']):
                        insights.append({
                            "type": "observation",
                            "description": line,
                            "confidence": "medium"
                        })
        
        return insights
    
    async def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """Call the LLM with the given prompt."""
        if self.provider == "gemini":
            return await self._call_gemini(prompt, temperature)
        elif self.provider == "openai":
            return await self._call_openai(prompt, temperature)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt, temperature)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    async def _call_gemini(self, prompt: str, temperature: float) -> str:
        """Call Google Gemini API using LangChain."""
        response = await self.client.ainvoke(prompt, temperature=temperature)
        return response.content
    
    async def _call_openai(self, prompt: str, temperature: float) -> str:
        """Call OpenAI API."""
        import asyncio
        
        loop = asyncio.get_event_loop()
        
        def _call():
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert data analyst and Python programmer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=4000
            )
            return response.choices[0].message.content
        
        return await loop.run_in_executor(None, _call)
    
    async def _call_anthropic(self, prompt: str, temperature: float) -> str:
        """Call Anthropic API."""
        import asyncio
        
        loop = asyncio.get_event_loop()
        
        def _call():
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=temperature,
                system="You are an expert data analyst and Python programmer.",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        return await loop.run_in_executor(None, _call)
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON object from text."""
        # Try to find JSON in code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            return json.loads(match.group(1))
        
        # Try to find JSON directly
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if match:
            return json.loads(match.group(0))
        
        raise ValueError("No JSON found in response")
    
    def _clean_code(self, code: str) -> str:
        """Clean up code by removing markdown formatting."""
        # Remove markdown code blocks
        code = re.sub(r'^```python\s*', '', code)
        code = re.sub(r'^```\s*', '', code)
        code = re.sub(r'```\s*$', '', code)
        
        # Strip whitespace
        code = code.strip()
        
        return code


class AgentThought:
    """Represents a single thought from the agent."""
    
    def __init__(self, thought_type: str, content: str, metadata: Dict[str, Any] = None):
        self.id = str(datetime.utcnow().timestamp())
        self.timestamp = datetime.utcnow().isoformat()
        self.type = thought_type  # "thinking", "action", "observation", "result", "error"
        self.content = content
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata
        }
