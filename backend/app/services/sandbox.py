"""
# Architect: Meet Kumar
# InsightAI - Docker Sandbox for Secure Code Execution
"""

import os
import json
import tempfile
import docker
from docker.errors import DockerException, ContainerError, ImageNotFound
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from app.core.config import settings


class DockerSandbox:
    """
    Secure Docker sandbox for executing Python code.
    
    This class provides a secure environment for running untrusted Python code
    by spinning up isolated Docker containers with strict resource limits.
    """
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Docker client."""
        try:
            self.client = docker.from_env()
        except DockerException as e:
            raise RuntimeError(f"Failed to connect to Docker daemon: {e}")
    
    async def execute_python_script(
        self,
        script: str,
        csv_path: str,
        timeout: int = None,
        memory_limit: str = None,
        cpu_limit: float = None,
        additional_files: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Execute a Python script in a secure Docker container.
        
        Args:
            script: Python code to execute
            csv_path: Path to the CSV file to mount (read-only)
            timeout: Execution timeout in seconds
            memory_limit: Docker memory limit (e.g., "512m")
            cpu_limit: CPU limit (e.g., 1.0 for 1 core)
            additional_files: Dict of {filename: content} for additional files
        
        Returns:
            Dict with execution results:
            {
                "success": bool,
                "output": str,
                "error": str (if failed),
                "execution_time": float,
                "files_generated": list
            }
        """
        timeout = timeout or settings.DOCKER_TIMEOUT
        memory_limit = memory_limit or settings.DOCKER_MEMORY_LIMIT
        cpu_limit = cpu_limit or settings.DOCKER_CPU_LIMIT
        
        container = None
        temp_dir = None
        start_time = datetime.utcnow()
        
        try:
            # Create temporary directory for script and outputs
            temp_dir = tempfile.mkdtemp(prefix="insightai_sandbox_")
            
            # Write the main script
            script_path = os.path.join(temp_dir, "analysis.py")
            with open(script_path, "w") as f:
                f.write(script)
            
            # Write additional files if provided
            if additional_files:
                for filename, content in additional_files.items():
                    file_path = os.path.join(temp_dir, filename)
                    with open(file_path, "w") as f:
                        f.write(content)
            
            # Prepare volumes
            volumes = {
                temp_dir: {"bind": "/app", "mode": "rw"},
            }
            
            # Mount CSV file if provided
            if csv_path and os.path.exists(csv_path):
                volumes[csv_path] = {"bind": "/data/input.csv", "mode": "ro"}
            
            # Ensure image exists
            try:
                self.client.images.get("python:3.11-slim")
            except ImageNotFound:
                # Pull image if not available
                await asyncio.to_thread(
                    self.client.images.pull,
                    "python:3.11-slim"
                )
            
            # Run container
            container = await asyncio.to_thread(
                self.client.containers.run,
                "python:3.11-slim",
                command=["python", "/app/analysis.py"],
                volumes=volumes,
                mem_limit=memory_limit,
                cpu_quota=int(cpu_limit * 100000),
                cpu_period=100000,
                network_mode="none",  # No network access for security
                read_only=False,  # Allow writing to /app for outputs
                detach=True,
                stdout=True,
                stderr=True,
            )
            
            # Wait for container to finish with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(container.wait, timeout=timeout),
                    timeout=timeout + 5  # Add buffer for Docker overhead
                )
            except asyncio.TimeoutError:
                # Container timed out
                return {
                    "success": False,
                    "output": "",
                    "error": f"Execution timed out after {timeout} seconds",
                    "execution_time": timeout,
                    "files_generated": []
                }
            
            # Get logs
            logs = await asyncio.to_thread(container.logs, stdout=True, stderr=True)
            logs_str = logs.decode("utf-8", errors="replace")
            
            # Check exit code
            exit_code = result.get("StatusCode", -1)
            
            # Get generated files
            files_generated = []
            output_dir = os.path.join(temp_dir, "outputs")
            if os.path.exists(output_dir):
                files_generated = os.listdir(output_dir)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            if exit_code == 0:
                return {
                    "success": True,
                    "output": logs_str,
                    "error": None,
                    "execution_time": execution_time,
                    "files_generated": files_generated,
                    "temp_dir": temp_dir
                }
            else:
                return {
                    "success": False,
                    "output": logs_str,
                    "error": f"Script exited with code {exit_code}",
                    "execution_time": execution_time,
                    "files_generated": files_generated
                }
                
        except ContainerError as e:
            return {
                "success": False,
                "output": "",
                "error": f"Container error: {str(e)}",
                "execution_time": (datetime.utcnow() - start_time).total_seconds(),
                "files_generated": []
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Execution error: {str(e)}",
                "execution_time": (datetime.utcnow() - start_time).total_seconds(),
                "files_generated": []
            }
            
        finally:
            # Clean up container
            if container:
                try:
                    await asyncio.to_thread(container.remove, force=True)
                except Exception:
                    pass  # Ignore cleanup errors
    
    async def validate_script(self, script: str) -> Dict[str, Any]:
        """
        Validate a Python script for syntax errors without executing.
        
        Args:
            script: Python code to validate
        
        Returns:
            Dict with validation results
        """
        import ast
        
        try:
            ast.parse(script)
            return {
                "valid": True,
                "error": None
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error at line {e.lineno}: {e.msg}"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def cleanup_temp_dir(self, temp_dir: str):
        """Clean up temporary directory."""
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


class SandboxManager:
    """
    Manager for handling multiple sandbox executions.
    """
    
    def __init__(self):
        self.sandboxes: Dict[str, DockerSandbox] = {}
        self.active_containers: Dict[str, Any] = {}
    
    def get_sandbox(self, session_id: str) -> DockerSandbox:
        """Get or create a sandbox for a session."""
        if session_id not in self.sandboxes:
            self.sandboxes[session_id] = DockerSandbox()
        return self.sandboxes[session_id]
    
    async def cancel_execution(self, session_id: str) -> bool:
        """Cancel an active execution."""
        if session_id in self.active_containers:
            container = self.active_containers[session_id]
            try:
                await asyncio.to_thread(container.stop, timeout=5)
                await asyncio.to_thread(container.remove, force=True)
                del self.active_containers[session_id]
                return True
            except Exception:
                return False
        return False
    
    def cleanup_session(self, session_id: str):
        """Clean up a session's resources."""
        if session_id in self.sandboxes:
            del self.sandboxes[session_id]
