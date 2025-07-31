"""
MCP Bridge Session Management Module.

This module provides session management functionality for MCP Bridge,
handling the complete lifecycle of bridging MCP servers with LLM services.
This includes MCP server connections, tool discovery, prompt building,
LLM interactions, and response handling with multi-turn conversations.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from mcpbridge.core.conversation import Conversation
from mcpbridge.core.llm_executor import LLMExecutor
from mcpbridge.core.tool_executor import ToolExecutor
from mcpbridge.llm.openai.parser import OpenAIParser
from mcpbridge.prompt.builder import PromptBuilder
from mcpbridge.utils.logging import get_mcpbridge_logger, log_json

if TYPE_CHECKING:
    from mcpbridge.core.context import Context

# Get configured logger for this module
logger = get_mcpbridge_logger(__name__)


class Session:
    """
    Manages a session for MCP Bridge operations.
    
    A session represents a complete interaction lifecycle that bridges MCP servers
    with LLM services. This includes:
    - MCP server connection and tool discovery
    - Prompt building with available tools
    - LLM interaction with the constructed prompt
    - Multi-turn conversation handling with tool execution
    - Response parsing and session cleanup
    
    Each session has a unique identifier for tracking and debugging purposes
    across both MCP and LLM interactions. The session orchestrates the complete
    workflow from initial prompt to final response.
    
    Attributes:
        id (str): Unique session identifier generated using UUID4
        ctx (Context): Application context containing configuration and parameters
        llm_executor (LLMExecutor): Executor for LLM interactions
        tools_executor (ToolExecutor): Executor for MCP tool operations
    """
    
    def __init__(self, ctx: Context) -> None:
        """
        Initialize a new MCP session.
        
        Creates a new session with a unique identifier and initializes the
        necessary executors for LLM and tool operations. The session ID is
        used throughout the lifecycle for logging and tracking purposes.
        
        Args:
            ctx (Context): The context containing MCP server configuration,
                          LLM settings, user prompt, and other session parameters
        """
        # Generate unique session identifier for tracking
        self.id = str(uuid.uuid4())
        self.ctx = ctx
        self.llm_executor = LLMExecutor(self.id)
        self.tools_executor = ToolExecutor(self.ctx)

    async def start(self) -> None:
        """
        Start the MCP session and establish connection with the server.
        
        This method performs the complete MCP Bridge workflow:
        1. Initializes the session with proper logging
        2. Establishes LLM executor context for resource management
        3. Executes the main conversation loop
        4. Handles session cleanup and error recovery
        
        Raises:
            Exception: If connection to the MCP server fails or session 
                      initialization encounters a critical error. LLM errors are 
                      caught and logged but do not interrupt the session.
        """
        # Log session startup with unique identifier
        logger.info(f"Starting session {self.id}")
        logger.debug(f"Session context: {self.ctx}")

        try:
            # Use async context manager for proper LLM executor lifecycle
            async with self.llm_executor:
                await self._run_conversation_loop()
        except Exception as e:
            logger.error(f"Session {self.id}: Critical error during session: {e}")
            raise
        finally:
            logger.info(f"Session {self.id}: Session completed")

    async def _run_conversation_loop(self):
        """
        Execute the main conversation loop between LLM and MCP tools.
        
        This method orchestrates the complete conversation flow:
        1. Retrieves available tools from MCP server
        2. Builds initial prompt with system and user messages
        3. Initializes conversation with proper message structure
        4. Executes the main conversation loop:
           - Sends conversation to LLM with available tools
           - Parses LLM response for tool calls
           - Executes tools and adds results to conversation
           - Continues until no more tool calls are needed
        
        The loop continues until the LLM response indicates no further
        tool calls are required, completing the conversation.
        
        The conversation maintains state through the Conversation object,
        which tracks all messages, tool calls, and results for context.
        """
        # Get tools info and build initial prompt
        tools_info = await self.tools_executor.get_tools_definition()
        prompt_builder = PromptBuilder(template_name="default")
        initial_prompt = prompt_builder.build_initial_prompt(user_prompt=self.ctx.prompt)

        # Initialize conversation with system and user messages
        conv = Conversation(session=self.id, system_prompt=initial_prompt["messages"][0]["content"])
        conv.add_user_message(initial_prompt["messages"][1]["content"])
        log_json(logger, conv.get_messages(), "Initial conversation messages")

        # First LLM interaction with available tools
        llm_response = await self.llm_executor.get_completion(conv, tools_info)
        if not llm_response:
            logger.error(f"Session {self.id}: failed to get initial LLM response. Aborting.")
            return

        conv.add_assistant_message(llm_response)
        log_json(logger, conv.get_messages(), "First LLM response messages")

        # Run conversation loop until no more tool calls are needed
        response_parser = OpenAIParser()
        while response_parser.need_tools_call(llm_response):
            # Extract and prepare tool calls from LLM response
            tool_calls = response_parser.prepare_tools_call(llm_response)

            # Execute each tool call and add results to conversation
            for tool_call in tool_calls:
                tool_result = await self.tools_executor.call_tool(tool_call)
                conv.add_tool_result(
                    tool_call["id"], 
                    tool_call["name"], 
                    tool_result["text_content"]
                )
            log_json(logger, conv.get_messages(), "Tool result messages")

            # Get next LLM response with updated conversation context
            llm_response = await self.llm_executor.get_completion(conv, tools_info)
            if not llm_response:
                logger.error(f"Session {self.id}: failed to get LLM response after tool call. Aborting conversation.")
                break

            conv.add_assistant_message(llm_response)
            log_json(logger, conv.get_messages(), "LLM response messages")
