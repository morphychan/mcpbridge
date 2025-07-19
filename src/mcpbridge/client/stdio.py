import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def run_stdio(command: str, args: list[str]):
    params = StdioServerParameters(
        command=command,
        args=args,
    )

    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            tools_response = await session.list_tools()
            print("Available tools:", [t.name for t in tools_response.tools])

            tools = tools_response.tools                  
            full_spec = [t.model_dump(by_alias=True) for t in tools]
            print(json.dumps(full_spec, indent=2, ensure_ascii=False))
            