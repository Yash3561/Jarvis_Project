"""
A.R.I.E.S. Core Orchestrator
The Master Strategist & Planner

This module implements the core intelligence layer that:
- Decomposes user intent into actionable plans
- Queries the Memory Core for context
- Generates multi-step, verifiable plans
- Selects appropriate tools from the Tool Belt
- Synthesizes final user responses
"""

import json
import re
import asyncio
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import google.generativeai as genai
from guardian import Guardian
from memory_core import MemoryCore
from tool_belt import ToolBelt

class IntentType(Enum):
    """Classification of user intent types"""
    SYSTEM_CONTROL = "system_control"
    WEB_NAVIGATION = "web_navigation"
    CODE_DEVELOPMENT = "code_development"
    FILE_OPERATION = "file_operation"
    INFORMATION_QUERY = "information_query"
    AUTOMATION = "automation"
    UNKNOWN = "unknown"

@dataclass
class ExecutionPlan:
    """Represents a verified execution plan"""
    intent: str
    steps: List[Dict[str, Any]]
    tools_required: List[str]
    estimated_time: str
    risk_level: str
    rollback_plan: Optional[str] = None

class AriesCore:
    """
    The Core Orchestrator - The Brain of A.R.I.E.S.
    
    This class is responsible for:
    1. Understanding user intent
    2. Planning execution strategies
    3. Coordinating with the Guardian for safety
    4. Managing the Memory Core for context
    5. Orchestrating the Tool Belt
    """
    
    def __init__(self, config, guardian: Guardian, memory_core: MemoryCore, tool_belt: ToolBelt):
        self.config = config
        self.guardian = guardian
        self.memory_core = memory_core
        self.tool_belt = tool_belt
        
        # Initialize Gemini 1.5 Pro
        genai.configure(api_key=config.gemini_api_key)
        self.llm = genai.GenerativeModel('gemini-1.5-pro')
        
        print("INFO: A.R.I.E.S. Core Orchestrator initialized with Gemini 1.5 Pro")
    
    async def process_intent(self, user_query: str, context: Optional[Dict] = None) -> str:
        """
        Main entry point for processing user intent
        
        Args:
            user_query: The user's request
            context: Optional context from previous interactions
            
        Returns:
            Response to the user
        """
        try:
            # Step 1: Analyze and classify intent
            intent_analysis = await self._analyze_intent(user_query)
            
            # Step 2: Query Memory Core for relevant context
            memory_context = await self._get_memory_context(user_query, intent_analysis)
            
            # Step 3: Generate execution plan
            execution_plan = await self._generate_execution_plan(
                user_query, intent_analysis, memory_context
            )
            
            # Step 4: Execute plan through Guardian
            result = await self._execute_plan(execution_plan)
            
            # Step 5: Update Memory Core with this interaction
            await self._update_memory(user_query, execution_plan, result)
            
            # Step 6: Synthesize response
            response = await self._synthesize_response(user_query, result, execution_plan)
            
            return response
            
        except Exception as e:
            error_msg = f"Critical error in A.R.I.E.S. Core: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return f"**System Error:** {error_msg}\n\nPlease try again or contact support."
    
    async def _analyze_intent(self, query: str) -> Dict[str, Any]:
        """Analyze user intent using Gemini 1.5 Pro"""
        
        prompt = f"""
        Analyze the following user query and classify it according to the A.R.I.E.S. intent system.
        
        User Query: "{query}"
        
        Please provide a JSON response with the following structure:
        {{
            "intent_type": "one of: system_control, web_navigation, code_development, file_operation, information_query, automation, unknown",
            "confidence": 0.0-1.0,
            "complexity": "simple, moderate, complex",
            "tools_needed": ["list", "of", "required", "tools"],
            "priority": "low, medium, high, critical",
            "description": "brief description of what the user wants"
        }}
        
        Be precise and thoughtful in your analysis.
        """
        
        response = await self.llm.generate_content_async(prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback analysis
                return {
                    "intent_type": "unknown",
                    "confidence": 0.5,
                    "complexity": "moderate",
                    "tools_needed": [],
                    "priority": "medium",
                    "description": "Unable to determine intent"
                }
        except json.JSONDecodeError:
            return {
                "intent_type": "unknown",
                "confidence": 0.3,
                "complexity": "moderate",
                "tools_needed": [],
                "priority": "medium",
                "description": "Intent analysis failed"
            }
    
    async def _get_memory_context(self, query: str, intent_analysis: Dict) -> Dict[str, Any]:
        """Query Memory Core for relevant context"""
        try:
            # Get relevant memories based on intent
            relevant_memories = await self.memory_core.search_relevant_memories(
                query, intent_analysis["intent_type"]
            )
            
            # Get project context if this is development-related
            project_context = None
            if intent_analysis["intent_type"] == "code_development":
                project_context = await self.memory_core.get_current_project_context()
            
            return {
                "relevant_memories": relevant_memories,
                "project_context": project_context,
                "user_preferences": await self.memory_core.get_user_preferences()
            }
        except Exception as e:
            print(f"[WARNING] Memory context retrieval failed: {e}")
            return {"relevant_memories": [], "project_context": None, "user_preferences": {}}
    
    async def _generate_execution_plan(self, query: str, intent_analysis: Dict, memory_context: Dict) -> ExecutionPlan:
        """Generate a detailed execution plan using Gemini 1.5 Pro"""
        
        context_summary = self._summarize_context(memory_context)
        
        prompt = f"""
        As A.R.I.E.S., generate a detailed execution plan for the following request:
        
        USER REQUEST: "{query}"
        INTENT ANALYSIS: {json.dumps(intent_analysis, indent=2)}
        MEMORY CONTEXT: {context_summary}
        
        Generate a JSON execution plan with this structure:
        {{
            "intent": "clear description of what we're accomplishing",
            "steps": [
                {{
                    "step_number": 1,
                    "action": "specific action to take",
                    "tool": "tool_name_to_use",
                    "parameters": {{"param1": "value1"}},
                    "verification": "how to verify this step succeeded",
                    "estimated_time": "time estimate"
                }}
            ],
            "tools_required": ["list", "of", "tools"],
            "estimated_time": "total time estimate",
            "risk_level": "low, medium, high",
            "rollback_plan": "how to undo if something goes wrong"
        }}
        
        Be specific, safe, and thorough. Consider the user's context and preferences.
        """
        
        response = await self.llm.generate_content_async(prompt)
        
        try:
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
                return ExecutionPlan(**plan_data)
            else:
                # Fallback plan
                return ExecutionPlan(
                    intent="Execute user request safely",
                    steps=[{
                        "step_number": 1,
                        "action": "Process request",
                        "tool": "ask_user_for_help",
                        "parameters": {"query": query},
                        "verification": "User confirms understanding",
                        "estimated_time": "1 minute"
                    }],
                    tools_required=["ask_user_for_help"],
                    estimated_time="1 minute",
                    risk_level="low"
                )
        except Exception as e:
            print(f"[ERROR] Plan generation failed: {e}")
            # Return safe fallback plan
            return ExecutionPlan(
                intent="Safely handle user request",
                steps=[{
                    "step_number": 1,
                    "action": "Request clarification",
                    "tool": "ask_user_for_help",
                    "parameters": {"query": f"Could you clarify: {query}"},
                    "verification": "User provides clarification",
                    "estimated_time": "1 minute"
                }],
                tools_required=["ask_user_for_help"],
                estimated_time="1 minute",
                risk_level="low"
            )
    
    def _summarize_context(self, memory_context: Dict) -> str:
        """Summarize memory context for the LLM"""
        summary = []
        
        if memory_context.get("relevant_memories"):
            summary.append(f"Found {len(memory_context['relevant_memories'])} relevant memories")
        
        if memory_context.get("project_context"):
            summary.append(f"Current project: {memory_context['project_context'].get('name', 'Unknown')}")
        
        if memory_context.get("user_preferences"):
            summary.append(f"User preferences available: {len(memory_context['user_preferences'])} items")
        
        return "; ".join(summary) if summary else "No relevant context found"
    
    async def _execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute the plan through the Guardian"""
        results = {
            "steps_completed": [],
            "steps_failed": [],
            "final_result": None,
            "execution_time": 0
        }
        
        for step in plan.steps:
            try:
                print(f"[A.R.I.E.S.] Executing step {step['step_number']}: {step['action']}")
                
                # Execute through Guardian for safety
                result = await self.guardian.execute_tool_safely(
                    step["tool"],
                    step["parameters"],
                    step["verification"]
                )
                
                results["steps_completed"].append({
                    "step": step,
                    "result": result,
                    "success": True
                })
                
            except Exception as e:
                error_msg = f"Step {step['step_number']} failed: {str(e)}"
                print(f"[ERROR] {error_msg}")
                
                results["steps_failed"].append({
                    "step": step,
                    "error": str(e),
                    "success": False
                })
                
                # If critical step fails, attempt rollback
                if plan.rollback_plan:
                    await self._attempt_rollback(plan.rollback_plan, results)
                break
        
        return results
    
    async def _attempt_rollback(self, rollback_plan: str, results: Dict):
        """Attempt to rollback failed operations"""
        print(f"[A.R.I.E.S.] Attempting rollback: {rollback_plan}")
        # Implementation will depend on specific rollback strategies
        pass
    
    async def _update_memory(self, query: str, plan: ExecutionPlan, result: Dict):
        """Update Memory Core with this interaction"""
        try:
            await self.memory_core.store_interaction(
                query=query,
                plan=plan,
                result=result,
                timestamp=asyncio.get_event_loop().time()
            )
        except Exception as e:
            print(f"[WARNING] Memory update failed: {e}")
    
    async def _synthesize_response(self, query: str, result: Dict, plan: ExecutionPlan) -> str:
        """Synthesize final response to user"""
        
        if result["steps_failed"]:
            # Handle failure case
            failed_steps = [step["step"]["action"] for step in result["steps_failed"]]
            response = f"""
**Task Partially Completed**

I was able to complete some steps but encountered issues with:
- {', '.join(failed_steps)}

**What was accomplished:**
{self._format_completed_steps(result["steps_completed"])}

**Next steps:**
Please let me know if you'd like me to retry the failed steps or if you need help troubleshooting.
            """
        else:
            # Success case
            response = f"""
**Task Completed Successfully!**

I've successfully completed your request: "{query}"

**What was accomplished:**
{self._format_completed_steps(result["steps_completed"])}

**Total execution time:** {plan.estimated_time}

Is there anything else you'd like me to help you with?
            """
        
        return response.strip()
    
    def _format_completed_steps(self, completed_steps: List[Dict]) -> str:
        """Format completed steps for display"""
        if not completed_steps:
            return "No steps were completed."
        
        formatted = []
        for step_info in completed_steps:
            step = step_info["step"]
            formatted.append(f"• **{step['action']}** - {step['estimated_time']}")
        
        return "\n".join(formatted)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "status": "operational",
            "guardian_status": "active",
            "memory_core_status": "active",
            "tool_belt_status": "active",
            "llm_status": "connected"
        }
