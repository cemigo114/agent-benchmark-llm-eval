"""OpenAI-based agent implementation."""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import openai
from openai import AsyncOpenAI

from ..utils.logging import get_logger
from .base import BaseAgent, Message, AgentResponse, ToolCall

logger = get_logger(__name__)


class OpenAIAgent(BaseAgent):
    """Agent implementation using OpenAI's API."""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        self.client = AsyncOpenAI(api_key=api_key)
        
    async def generate_response(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AgentResponse:
        """Generate a response using OpenAI's chat completion API."""
        
        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages)
            
            # Prepare request parameters
            request_params = {
                "model": self.model_name,
                "messages": openai_messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "timeout": self.timeout,
                **self.extra_params,
                **kwargs
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = self._convert_tools(tools)
                request_params["tool_choice"] = "auto"
            
            logger.info(f"Making OpenAI request with {len(openai_messages)} messages")
            
            # Make the API request
            response = await self.client.chat.completions.create(**request_params)
            
            # Convert response to our format
            choice = response.choices[0]
            message = choice.message
            
            # Extract tool calls if any
            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append(ToolCall(
                        id=tc.id,
                        function=tc.function.name,
                        arguments=json.loads(tc.function.arguments)
                    ))
            
            # Create response message
            response_message = Message(
                role="assistant",
                content=message.content or "",
                tool_calls=[{
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function,
                        "arguments": tc.arguments
                    }
                } for tc in tool_calls] if tool_calls else None
            )
            
            return AgentResponse(
                message=response_message,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None
            )
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            raise
    
    async def stream_response(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI."""
        
        try:
            openai_messages = self._convert_messages(messages)
            
            request_params = {
                "model": self.model_name,
                "messages": openai_messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": True,
                **self.extra_params,
                **kwargs
            }
            
            if tools:
                request_params["tools"] = self._convert_tools(tools)
                request_params["tool_choice"] = "auto"
            
            async for chunk in await self.client.chat.completions.create(**request_params):
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming OpenAI response: {e}")
            raise
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert our message format to OpenAI format."""
        openai_messages = []
        
        for msg in messages:
            openai_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            # Add tool calls if present
            if msg.tool_calls:
                openai_msg["tool_calls"] = msg.tool_calls
            
            # Add tool call ID if present (for tool responses)
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
                
            # Add name if present (for tool responses)
            if msg.name:
                openai_msg["name"] = msg.name
                
            openai_messages.append(openai_msg)
        
        return openai_messages
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to OpenAI format."""
        openai_tools = []
        
        for tool in tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            openai_tools.append(openai_tool)
        
        return openai_tools