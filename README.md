# MCPBridge

A lightweight Model Context Protocol (MCP) host that bridges MCP servers with LLM services.

## Overview

MCPBridge is a command-line tool that enables seamless integration between Model Context Protocol (MCP) servers and Large Language Models (LLMs). It provides a lightweight solution for connecting MCP-compatible tools with AI services through a simple CLI interface.

## Features

- **MCP Server Integration**: Connect to MCP servers using stdio transport
- **LLM Integration**: Built-in support for OpenAI-compatible LLM services
- **Tool Discovery**: Automatic discovery and registration of MCP tools
- **Multi-turn Conversations**: Support for conversational interactions with tool execution
- **Session Management**: Complete lifecycle management of MCP-LLM bridging sessions
- **Command-line Interface**: Easy-to-use CLI with Typer framework

## Requirements

- Python 3.13 or higher
- MCP-compatible server implementations
- OpenAI API key (or compatible service)

## Installation

### Using pip

```bash
pip install mcpbridge
```

### From source

```bash
git clone <repository-url>
cd mcpbridge
pip install -e .
```

## Configuration

Set the following environment variables for LLM configuration:

```bash
# Required
export MCPBRIDGE_LLM_API_KEY="your-api-key-here"

# Optional (with defaults)
export MCPBRIDGE_LLM_BASE_URL="https://api.openai.com/v1"  # default
export MCPBRIDGE_LLM_MODEL="gpt-4"                         # default
export MCPBRIDGE_LLM_TEMPERATURE="1.0"                     # default
export MCPBRIDGE_LLM_MAX_TOKENS="4096"                     # default
export MCPBRIDGE_LLM_TIMEOUT="120.0"                       # default
```

## Usage

### Basic Usage

Start an MCP server with tools and provide a prompt:

```bash
mcpbridge --prompt "Your prompt here" mcpserver stdio \
  -t "toolname python /path/to/server.py"
```

### Multiple Tools

You can specify multiple tools:

```bash
mcpbridge --prompt "Analyze this data" mcpserver stdio \
  -t "filesystem python /path/to/filesystem_server.py" \
  -t "database python /path/to/database_server.py"
```

### Command Structure

```
mcpbridge [--prompt PROMPT] mcpserver stdio -t TOOL_DEFINITION...
```

Where `TOOL_DEFINITION` follows the format: `"name command path"`

### Examples

1. **File system operations**:
   ```bash
   mcpbridge --prompt "List files in current directory" mcpserver stdio \
     -t "filesystem python /path/to/filesystem_mcp_server.py"
   ```

2. **Database operations**:
   ```bash
   mcpbridge --prompt "Query user data" mcpserver stdio \
     -t "database python /path/to/database_mcp_server.py"
   ```

3. **Multiple tool integration**:
   ```bash
   mcpbridge --prompt "Create a report from database and save to file" mcpserver stdio \
     -t "database python /path/to/db_server.py" \
     -t "filesystem python /path/to/fs_server.py"
   ```

### Dependencies

- `mcp[cli]>=1.12.0`: Model Context Protocol implementation
- `typer[all]>=0.9.0`: CLI framework
- `aiohttp>=3.8.0`: Async HTTP client

### Running from Source

```bash
# Install in development mode
pip install -e .

# Run directly
python -m mcpbridge --prompt "test" mcpserver stdio -t "test python test_server.py"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Version

Current version: 0.1.0

## Support

For issues and questions, please open an issue on the project repository.
