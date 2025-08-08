"""Anthropic Claude-based agent implementation."""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import anthropic

from ..utils.logging import get_logger
from .base import BaseAgent, Message, AgentResponse, ToolCall

logger = get_logger(__name__)


class AnthropicAgent(BaseAgent):
    """Agent implementation using Anthropic's Claude API."""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        
    async def generate_response(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AgentResponse:
        """Generate a response using Anthropic's messages API."""
        
        try:
            # Convert messages to Anthropic format
            system_message, claude_messages = self._convert_messages(messages)
            
            # Prepare request parameters
            request_params = {
                "model": self.model_name,
                "messages": claude_messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                **self.extra_params,
                **kwargs
            }
            
            # Add system message if present
            if system_message:
                request_params["system"] = system_message
            
            # Add tools if provided
            if tools:
                request_params["tools"] = self._convert_tools(tools)
            
            logger.info(f"Making Anthropic request with {len(claude_messages)} messages")
            
            # Make the API request
            response = await self.client.messages.create(**request_params)
            
            # Extract content and tool calls
            content = ""
            tool_calls = []
            
            for content_block in response.content:
                if content_block.type == "text":
                    content += content_block.text
                elif content_block.type == "tool_use":
                    tool_calls.append(ToolCall(
                        id=content_block.id,
                        function=content_block.name,
                        arguments=content_block.input
                    ))
            
            # Create response message
            response_message = Message(
                role="assistant",
                content=content,
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
                finish_reason=response.stop_reason,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating Anthropic response: {e}")
            raise
    
    async def stream_response(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from Anthropic."""
        
        try:
            system_message, claude_messages = self._convert_messages(messages)
            
            request_params = {
                "model": self.model_name,
                "messages": claude_messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": True,
                **self.extra_params,
                **kwargs
            }
            
            if system_message:
                request_params["system"] = system_message
                
            if tools:
                request_params["tools"] = self._convert_tools(tools)
            
            async with self.client.messages.stream(**request_params) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Error streaming Anthropic response: {e}")
            raise
    
    def _convert_messages(self, messages: List[Message]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Convert our message format to Anthropic format."""
        system_message = None
        claude_messages = []
        
        for msg in messages:
            if msg.role == "system":
                # Anthropic handles system messages separately
                system_message = msg.content
                continue
                
            claude_msg = {
                "role": msg.role,
                "content": []
            }
            
            # Add text content
            if msg.content:
                claude_msg["content"].append({
                    "type": "text",
                    "text": msg.content
                })
            
            # Add tool calls if present
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    claude_msg["content"].append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": tc["function"]["arguments"]
                    })
            
            # Handle tool results
            if msg.role == "tool":
                claude_msg = {
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content
                    }]
                }
            
            # Simplify content if only one text block
            if len(claude_msg["content"]) == 1 and claude_msg["content"][0]["type"] == "text":
                claude_msg["content"] = claude_msg["content"][0]["text"]
            
            claude_messages.append(claude_msg)
        
        return system_message, claude_messages
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to Anthropic format."""
        claude_tools = []
        
        for tool in tools:
            claude_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["parameters"]
            }
            claude_tools.append(claude_tool)
        
        return claude_tools