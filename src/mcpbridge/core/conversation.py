"""
Conversation management for MCP (Model Context Protocol) bridge.

This module provides the Conversation class for managing message sequences
in AI model conversations. It handles different message types (system, user,
assistant, tool) and provides methods for building and retrieving conversation
contexts that can be sent to AI models.
"""

from typing import Dict, Any, List, Union
from mcpbridge.core.message_models import SystemMessage, UserMessage, AssistantMessage, ToolCallResult, ToolCall

# Type alias for all supported message types
Message = Union[SystemMessage, UserMessage, AssistantMessage, ToolCallResult]


class Conversation:
    """
    Manages the sequence of messages in a conversation with an AI model.
    
    This class provides a structured way to build and maintain conversation
    history, including system prompts, user inputs, assistant responses,
    and tool call results. It ensures proper message ordering and format
    for compatibility with various AI model APIs.
    
    Attributes:
        session: Unique identifier for the conversation session
        messages: List of all messages in the conversation
    """
    
    def __init__(self, session: str, system_prompt: str = None) -> None:
        """
        Initialize a new conversation.
        
        Args:
            session: Unique identifier for the conversation session
            system_prompt: Optional system prompt to set the AI model's behavior
        """
        self.session = session
        self.messages: List[Message] = []
        if system_prompt:
            self.messages.append(SystemMessage(content=system_prompt))

    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the conversation.
        
        User messages represent input from the human user and are the primary
        messages that the AI model responds to.
        
        Args:
            content: The user's input text
        """
        self.messages.append(UserMessage(content=content))

    def add_assistant_message(self, response: dict) -> None:
        """
        Add an assistant message to the conversation.
        
        Assistant messages contain the AI model's responses. They can include
        both text content and tool calls. Either content or tool_calls (or both)
        can be provided.
        
        Args:
            response: The response from the LLM
        """
        if isinstance(response, dict) and "choices" in response and len(response["choices"]) > 0:
            message = response["choices"][0]["message"]
            
            if "tool_calls" in message and message["tool_calls"]:
                self.messages.append(AssistantMessage(content=message["content"], tool_calls=message["tool_calls"]))
            else:
                self.messages.append(AssistantMessage(content=message["content"]))

    def add_tool_result(self, tool_call_id: str, name: str, content: str) -> None:
        """
        Add a tool result message to the conversation.
        
        Tool result messages contain the output from executed tool calls.
        They provide feedback to the assistant about the outcome of tool
        executions.
        
        Args:
            tool_call_id: ID of the tool call this result corresponds to
            name: The name of the tool that was called
            content: The result or output from the tool execution
        """
        self.messages.append(ToolCallResult(tool_call_id=tool_call_id, name=name, content=content))

    def get_messages(self) -> List[dict]:
        """
        Get the list of messages in the conversation as dictionaries.
        
        Returns a list of message dictionaries with None values excluded,
        suitable for sending to AI model APIs.
        
        Returns:
            List of message dictionaries ready for API consumption
        """
        return [message.model_dump(exclude_none=True) for message in self.messages]
    
    def __len__(self) -> int:
        """
        Get the number of messages in the conversation.
        
        Returns:
            Total number of messages in the conversation
        """
        return len(self.messages)
    
    def __str__(self) -> str:
        """
        Get a string representation of the conversation.
        
        Returns:
            String showing session ID and message count
        """
        return f"Conversation(session={self.session}, {len(self.messages)})"