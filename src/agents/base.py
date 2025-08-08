"""Base agent class for LLM agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator

from pydantic import BaseModel


class Message(BaseModel):
    """Represents a conversation message."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class ToolCall(BaseModel):
    """Represents a tool function call."""
    id: str
    function: str
    arguments: Dict[str, Any]


class AgentResponse(BaseModel):
    """Response from an agent."""
    message: Message
    tool_calls: List[ToolCall] = []
    finish_reason: str
    usage: Optional[Dict[str, int]] = None


class BaseAgent(ABC):
    """Abstract base class for LLM agents."""
    
    def __init__(
        self,
        model_name: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        timeout: int = 60,
        **kwargs
    ):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.extra_params = kwargs
        
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AgentResponse:
        """Generate a response given conversation history and available tools."""
        pass
        
    @abstractmethod
    async def stream_response(
        self,
        messages: List[Message], 
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response token by token."""
        pass
    
    def format_system_prompt(self, domain: str, policies: List[str]) -> str:
        """Format the system prompt with domain-specific information."""
        base_prompt = f"""You are an AI assistant operating in the {domain} domain.

Your responsibilities:
1. Help users with their requests using available tools
2. Follow all domain-specific policies and guidelines
3. Be helpful, accurate, and professional
4. Ask for clarification when needed
5. Use tools appropriately to complete tasks

Domain Policies:
{chr(10).join(f"- {policy}" for policy in policies)}

Always prioritize user safety and policy compliance."""
        
        return base_prompt
    
    def format_tool_result(self, tool_name: str, result: Any) -> str:
        """Format tool execution results for the conversation."""
        if isinstance(result, dict):
            if result.get("success", True):
                return f"Tool '{tool_name}' executed successfully: {result.get('data', result)}"
            else:
                return f"Tool '{tool_name}' failed: {result.get('error', 'Unknown error')}"
        else:
            return f"Tool '{tool_name}' result: {result}"