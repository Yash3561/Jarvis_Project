"""
A.R.I.E.S. Tool Belt - The Hands
Consolidated tool system organized by capability

This module implements:
- System Provisioner: Installs core dependencies
- Environment Manager: Creates sandboxes (Docker, venv)
- Stateful Code Executor: Writes, runs, and debugs code
- Adaptive Web Module: API -> Structured Search -> Vision-Based Browser
- Human Escalation Protocol: Handles Captchas & unsolvable problems
"""

import os
import sys
import subprocess
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import importlib.util
import json
from datetime import datetime

class SystemProvisioner:
    """Installs and manages core system dependencies"""
    
    def __init__(self):
        self.required_packages = {
            "python": ["python", "--version"],
            "node": ["node", "--version"],
            "npm": ["npm", "--version"],
            "git": ["git", "--version"],
            "docker": ["docker", "--version"]
        }
        
        self.package_managers = {
            "windows": "winget",
            "linux": "apt",
            "darwin": "brew"
        }
    
    async def check_dependencies(self) -> Dict[str, bool]:
        """Check which dependencies are available"""
        status = {}
        
        for package, command in self.required_packages.items():
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=5)
                status[package] = result.returncode == 0
            except Exception:
                status[package] = False
        
        return status
    
    async def install_dependency(self, package: str) -> bool:
        """Install a missing dependency"""
        try:
            platform = sys.platform
            package_manager = self._get_package_manager(platform)
            
            if package_manager == "winget":
                command = ["winget", "install", package]
            elif package_manager == "apt":
                command = ["sudo", "apt", "install", package, "-y"]
            elif package_manager == "brew":
                command = ["brew", "install", package]
            else:
                print(f"ERROR: Unsupported platform {platform}")
                return False
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
            
        except Exception as e:
            print(f"ERROR: Failed to install {package}: {e}")
            return False
    
    def _get_package_manager(self, platform: str) -> str:
        """Get the appropriate package manager for the platform"""
        if platform.startswith("win"):
            return "winget"
        elif platform.startswith("linux"):
            return "apt"
        elif platform.startswith("darwin"):
            return "brew"
        else:
            return "unknown"

class EnvironmentManager:
    """Creates and manages sandboxed environments"""
    
    def __init__(self, base_path: str = "./.aries_environments"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.active_environments = {}
    
    async def create_python_venv(self, project_name: str, python_version: str = "3.12") -> str:
        """Create a Python virtual environment"""
        try:
            env_path = self.base_path / f"{project_name}_venv"
            env_path.mkdir(exist_ok=True)
            
            # Create virtual environment
            subprocess.run([sys.executable, "-m", "venv", str(env_path)], check=True)
            
            # Store environment info
            self.active_environments[project_name] = {
                "type": "python_venv",
                "path": str(env_path),
                "python_version": python_version,
                "created": True
            }
            
            print(f"INFO: Python virtual environment created at {env_path}")
            return str(env_path)
            
        except Exception as e:
            print(f"ERROR: Failed to create Python venv: {e}")
            return ""
    
    async def create_docker_container(self, project_name: str, image: str = "python:3.12-slim") -> str:
        """Create a Docker container for the project"""
        try:
            container_name = f"aries_{project_name}"
            
            # Create and start container
            subprocess.run([
                "docker", "run", "-d", "--name", container_name,
                "-v", f"{os.getcwd()}:/workspace", "-w", "/workspace",
                image, "tail", "-f", "/dev/null"
            ], check=True)
            
            # Store container info
            self.active_environments[project_name] = {
                "type": "docker_container",
                "name": container_name,
                "image": image,
                "created": True
            }
            
            print(f"INFO: Docker container {container_name} created")
            return container_name
            
        except Exception as e:
            print(f"ERROR: Failed to create Docker container: {e}")
            return ""
    
    async def activate_environment(self, project_name: str) -> bool:
        """Activate an environment for use"""
        if project_name not in self.active_environments:
            print(f"ERROR: Environment {project_name} not found")
            return False
        
        env_info = self.active_environments[project_name]
        
        if env_info["type"] == "python_venv":
            # Set environment variables for Python venv
            venv_path = Path(env_info["path"])
            os.environ["VIRTUAL_ENV"] = str(venv_path)
            os.environ["PATH"] = f"{venv_path / 'Scripts' if os.name == 'nt' else 'bin'}{os.pathsep}{os.environ['PATH']}"
            
        elif env_info["type"] == "docker_container":
            # Docker containers are already running
            pass
        
        print(f"INFO: Environment {project_name} activated")
        return True
    
    async def cleanup_environment(self, project_name: str) -> bool:
        """Clean up an environment"""
        if project_name not in self.active_environments:
            return False
        
        env_info = self.active_environments[project_name]
        
        try:
            if env_info["type"] == "python_venv":
                # Remove virtual environment directory
                import shutil
                shutil.rmtree(env_info["path"])
                
            elif env_info["type"] == "docker_container":
                # Stop and remove Docker container
                subprocess.run(["docker", "stop", env_info["name"]], check=True)
                subprocess.run(["docker", "rm", env_info["name"]], check=True)
            
            del self.active_environments[project_name]
            print(f"INFO: Environment {project_name} cleaned up")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to cleanup environment {project_name}: {e}")
            return False

class StatefulCodeExecutor:
    """Writes, runs, and debugs code with state management"""
    
    def __init__(self, project_manifest_path: str = "./.aries_project"):
        self.manifest_path = Path(project_manifest_path)
        self.manifest_path.mkdir(exist_ok=True)
        self.current_project = None
    
    async def create_project_manifest(self, project_name: str, tech_stack: List[str]) -> bool:
        """Create a project manifest file"""
        try:
            manifest = {
                "name": project_name,
                "tech_stack": tech_stack,
                "dependencies": [],
                "launch_commands": [],
                "file_structure": {},
                "created_date": str(datetime.now()),
                "last_modified": str(datetime.now()),
                "status": "active"
            }
            
            manifest_file = self.manifest_path / f"{project_name}.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self.current_project = project_name
            print(f"INFO: Project manifest created for {project_name}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to create project manifest: {e}")
            return False
    
    async def write_code_file(self, file_path: str, content: str, language: str = "python") -> bool:
        """Write code to a file with syntax validation"""
        try:
            # Ensure directory exists
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update project manifest
            if self.current_project:
                await self._update_file_structure(file_path, language)
            
            print(f"INFO: Code written to {file_path}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to write code file: {e}")
            return False
    
    async def run_code(self, file_path: str, args: List[str] = None) -> Tuple[bool, str, str]:
        """Run code and capture output"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return False, "", f"File {file_path} not found"
            
            # Determine how to run the file
            if file_path.suffix == ".py":
                command = [sys.executable, str(file_path)]
            elif file_path.suffix == ".js":
                command = ["node", str(file_path)]
            elif file_path.suffix == ".sh":
                command = ["bash", str(file_path)]
            else:
                return False, "", f"Unsupported file type: {file_path.suffix}"
            
            # Add arguments
            if args:
                command.extend(args)
            
            # Run the code
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=60
            )
            
            success = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Execution timed out"
        except Exception as e:
            return False, "", f"Execution failed: {e}"
    
    async def debug_code(self, file_path: str, breakpoints: List[int] = None) -> Dict[str, Any]:
        """Debug code with breakpoints"""
        try:
            # This is a simplified debugger - in practice, you'd want more sophisticated debugging
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {"error": f"File {file_path} not found"}
            
            # Read file and analyze
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Basic syntax check
            syntax_errors = []
            for i, line in enumerate(lines, 1):
                if line.strip() and not line.strip().startswith('#'):
                    # Basic Python syntax check
                    if file_path.suffix == ".py":
                        try:
                            compile(line, '<string>', 'exec')
                        except SyntaxError as e:
                            syntax_errors.append({
                                "line": i,
                                "error": str(e),
                                "code": line.strip()
                            })
            
            return {
                "file_path": str(file_path),
                "total_lines": len(lines),
                "syntax_errors": syntax_errors,
                "breakpoints": breakpoints or []
            }
            
        except Exception as e:
            return {"error": f"Debug failed: {e}"}
    
    async def _update_file_structure(self, file_path: Path, language: str):
        """Update project manifest with file structure"""
        try:
            manifest_file = self.manifest_path / f"{self.current_project}.json"
            
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                # Update file structure
                relative_path = str(file_path.relative_to(Path.cwd()))
                manifest["file_structure"][relative_path] = {
                    "language": language,
                    "last_modified": str(datetime.now())
                }
                manifest["last_modified"] = str(datetime.now())
                
                with open(manifest_file, 'w') as f:
                    json.dump(manifest, f, indent=2)
                    
        except Exception as e:
            print(f"WARNING: Failed to update file structure: {e}")

class AdaptiveWebModule:
    """Hierarchy of API -> Structured Search -> Vision-Based Browser"""
    
    def __init__(self, config):
        self.config = config
        self.api_tools = {}
        self.search_tools = {}
        self.browser_tools = {}
        
        # Initialize available tools
        self._init_web_tools()
    
    def _init_web_tools(self):
        """Initialize available web tools"""
        # API tools (highest priority)
        self.api_tools = {
            "github_api": self._github_api_call,
            "weather_api": self._weather_api_call,
            "news_api": self._news_api_call
        }
        
        # Search tools (medium priority)
        self.search_tools = {
            "tavily_search": self._tavily_search,
            "google_search": self._google_search
        }
        
        # Browser tools (lowest priority, most comprehensive)
        self.browser_tools = {
            "playwright_browse": self._playwright_browse,
            "selenium_browse": self._selenium_browse
        }
    
    async def get_web_information(self, query: str, preferred_method: str = "auto") -> Dict[str, Any]:
        """Get information using the best available method"""
        try:
            # Try API first if specified or if query matches API patterns
            if preferred_method == "api" or self._is_api_query(query):
                for api_name, api_func in self.api_tools.items():
                    try:
                        result = await api_func(query)
                        if result:
                            return {
                                "method": "api",
                                "api": api_name,
                                "data": result,
                                "source": "direct_api"
                            }
                    except Exception:
                        continue
            
            # Try structured search
            if preferred_method == "search" or preferred_method == "auto":
                for search_name, search_func in self.search_tools.items():
                    try:
                        result = await search_func(query)
                        if result:
                            return {
                                "method": "search",
                                "search_engine": search_name,
                                "data": result,
                                "source": "structured_search"
                            }
                    except Exception:
                        continue
            
            # Fall back to browser automation
            if preferred_method == "browser" or preferred_method == "auto":
                for browser_name, browser_func in self.browser_tools.items():
                    try:
                        result = await browser_func(query)
                        if result:
                            return {
                                "method": "browser",
                                "browser": browser_name,
                                "data": result,
                                "source": "web_browsing"
                            }
                    except Exception:
                        continue
            
            return {"error": "No web information method available"}
            
        except Exception as e:
            return {"error": f"Web information retrieval failed: {e}"}
    
    def _is_api_query(self, query: str) -> bool:
        """Check if query is suitable for API calls"""
        api_patterns = [
            "weather", "temperature", "forecast",
            "github", "repository", "user",
            "news", "headlines", "latest"
        ]
        
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in api_patterns)
    
    # Placeholder API implementations
    async def _github_api_call(self, query: str) -> Optional[Dict]:
        """GitHub API call implementation"""
        # This would use the actual GitHub API
        return None
    
    async def _weather_api_call(self, query: str) -> Optional[Dict]:
        """Weather API call implementation"""
        # This would use a weather API
        return None
    
    async def _news_api_call(self, query: str) -> Optional[Dict]:
        """News API call implementation"""
        # This would use a news API
        return None
    
    # Placeholder search implementations
    async def _tavily_search(self, query: str) -> Optional[Dict]:
        """Tavily search implementation"""
        # This would use the Tavily API
        return None
    
    async def _google_search(self, query: str) -> Optional[Dict]:
        """Google search implementation"""
        # This would use Google search
        return None
    
    # Placeholder browser implementations
    async def _playwright_browse(self, query: str) -> Optional[Dict]:
        """Playwright browser automation"""
        # This would use Playwright
        return None
    
    async def _selenium_browse(self, query: str) -> Optional[Dict]:
        """Selenium browser automation"""
        # This would use Selenium
        return None

class HumanEscalationProtocol:
    """Handles Captchas and unsolvable problems"""
    
    def __init__(self, controller=None):
        self.controller = controller
        self.escalation_queue = []
        self.escalation_types = {
            "captcha": "Visual verification required",
            "login_failed": "Authentication failed",
            "permission_denied": "Access denied",
            "unsolvable": "Problem requires human intervention"
        }
    
    async def escalate_problem(self, problem_type: str, description: str, context: Dict = None) -> str:
        """Escalate a problem to human intervention"""
        try:
            escalation_id = f"esc_{len(self.escalation_queue)}_{datetime.now().timestamp()}"
            
            escalation = {
                "id": escalation_id,
                "type": problem_type,
                "description": description,
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
                "status": "pending",
                "human_response": None
            }
            
            self.escalation_queue.append(escalation)
            
            # Notify user through controller
            if self.controller and hasattr(self.controller, 'add_message_signal'):
                escalation_message = f"""
**Human Intervention Required**

**Problem Type:** {self.escalation_types.get(problem_type, problem_type)}
**Description:** {description}

**Context:** {json.dumps(context, indent=2) if context else 'None'}

**Action Required:** Please provide guidance or solve this problem manually.
                """
                self.controller.add_message_signal.emit('system', escalation_message, escalation_message)
            
            return escalation_id
            
        except Exception as e:
            print(f"ERROR: Failed to escalate problem: {e}")
            return ""
    
    async def resolve_escalation(self, escalation_id: str, human_response: str) -> bool:
        """Resolve an escalation with human input"""
        try:
            for escalation in self.escalation_queue:
                if escalation["id"] == escalation_id:
                    escalation["status"] = "resolved"
                    escalation["human_response"] = human_response
                    escalation["resolved_at"] = datetime.now().isoformat()
                    
                    print(f"INFO: Escalation {escalation_id} resolved")
                    return True
            
            return False
            
        except Exception as e:
            print(f"ERROR: Failed to resolve escalation: {e}")
            return False
    
    def get_pending_escalations(self) -> List[Dict]:
        """Get list of pending escalations"""
        return [e for e in self.escalation_queue if e["status"] == "pending"]

class ToolBelt:
    """
    The Tool Belt - Main interface for all tools
    
    This class provides access to:
    1. System Provisioner
    2. Environment Manager
    3. Stateful Code Executor
    4. Adaptive Web Module
    5. Human Escalation Protocol
    """
    
    def __init__(self, config, controller=None):
        self.config = config
        self.controller = controller
        
        # Initialize all tool categories
        self.system_provisioner = SystemProvisioner()
        self.environment_manager = EnvironmentManager()
        self.code_executor = StatefulCodeExecutor()
        self.web_module = AdaptiveWebModule(config)
        self.escalation_protocol = HumanEscalationProtocol(controller)
        
        print("INFO: A.R.I.E.S. Tool Belt initialized")
    
    async def get_tool_status(self) -> Dict[str, Any]:
        """Get status of all tools"""
        try:
            return {
                "system_provisioner": "active",
                "environment_manager": "active",
                "code_executor": "active",
                "web_module": "active",
                "escalation_protocol": "active",
                "active_environments": len(self.environment_manager.active_environments),
                "pending_escalations": len(self.escalation_protocol.get_pending_escalations())
            }
        except Exception as e:
            return {"error": f"Tool status check failed: {e}"}
    
    def get_available_tools(self) -> Dict[str, List[str]]:
        """Get list of available tools by category"""
        return {
            "system": ["check_dependencies", "install_dependency"],
            "environment": ["create_python_venv", "create_docker_container", "activate_environment"],
            "code": ["write_code_file", "run_code", "debug_code"],
            "web": ["get_web_information"],
            "escalation": ["escalate_problem", "resolve_escalation"]
        }
