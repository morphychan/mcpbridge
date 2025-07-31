"""
Message models for MCP (Model Context Protocol) bridge.

This module defines the core data structures used for communication between
the MCP bridge and various AI models. It includes models for different message
types (system, user, assistant, tool) and tool call structures that follow
the OpenAI API format for compatibility.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel


class FunctionCall(BaseModel):
    """
    Represents a function call to a tool.
    
    This model encapsulates the details of a function invocation, including
    the function name and its arguments. The arguments are stored as a JSON
    string to maintain flexibility with different argument structures.
    
    Attributes:
        name: The name of the function to be called
        arguments: JSON string containing the function arguments
    """
    name: str
    arguments: str


class ToolCall(BaseModel):
    """
    Represents a tool call request made by the assistant.
    
    This model follows the OpenAI API format for tool calls, containing
    a unique identifier and the function call details. Tool calls are used
    when the assistant needs to invoke external tools or functions.
    
    Attributes:
        id: Unique identifier for the tool call
        type: Type of the tool call (currently only "function" is supported)
        function: The function call details
    """
    id: str
    type: Literal["function"] = "function"
    function: FunctionCall


class SystemMessage(BaseModel):
    """
    Represents a system message with the 'system' role.
    
    System messages are used to provide instructions, context, or configuration
    to the AI model. These messages typically set the behavior and constraints
    for the conversation.
    
    Attributes:
        role: Message role, always "system"
        content: The system instruction or context content
    """
    role: Literal["system"] = "system"
    content: str


class UserMessage(BaseModel):
    """
    Represents a user message with the 'user' role.
    
    User messages contain the input from the human user. These are the primary
    messages that the AI model responds to in a conversation.
    
    Attributes:
        role: Message role, always "user"
        content: The user's input content
    """
    role: Literal["user"] = "user"
    content: str


class AssistantMessage(BaseModel):
    """
    Represents an assistant message with the 'assistant' role.
    
    Assistant messages contain the AI model's responses to user messages.
    They can include both text content and tool calls. The content is optional
    because the assistant might only make tool calls without providing text.
    
    Attributes:
        role: Message role, always "assistant"
        content: Optional text response from the assistant
        tool_calls: Optional list of tool calls made by the assistant
    """
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

class ToolCallResult(BaseModel):
    """
    Represents a tool call result with the 'tool' role.
    
    Tool call results contain the results of tool calls made by the assistant.
    They are used to provide feedback to the assistant about the outcome
    of executed tool calls.
    
    Attributes:
        role: Message role, always "tool"
        tool_call_id: ID of the tool call this result corresponds to
        content: The result or output from the tool execution
    """
    role: Literal["tool"] = "tool"
    tool_call_id: str
    name: str
    content: str
