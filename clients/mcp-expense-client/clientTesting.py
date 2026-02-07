import asyncio
import json
import os

# MCP + LangChain imports
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage, HumanMessage

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()



# Read FastMCP Cloud API key from environment
# This key is required to authenticate with remote FastMCP servers
FAST_MCP_API_KEY = os.getenv("FAST_MCP_API_KEY")

# ─────────────────────────────────────────────
# MCP SERVER CONFIGURATION
# ─────────────────────────────────────────────
# We are connecting to TWO MCP servers:
# 1. A local MCP server (math) via stdio
# 2. A remote FastMCP Cloud server (expense) via HTTP
SERVERS = { 
    "math": {
        # Local MCP server using stdio transport
        # fastmcp is launched as a subprocess using `uv run`
        "transport": "stdio",
        "command": "uv",
        "args": [
            "run",
            "fastmcp",
            "run",
            "servers/mcp-math-server/main.py"
       ]
    },
    "expense": {
        # Remote MCP server hosted on FastMCP Cloud
        # Uses streamable HTTP transport
        "transport": "streamable_http",  
        "url": "https://simple-addition.fastmcp.app/mcp",
        # Authorization header MUST contain Bearer token
        "headers": {
            "Authorization": f"Bearer {FAST_MCP_API_KEY}"
        }
    }
}

# ─────────────────────────────────────────────
# MAIN ASYNC ENTRYPOINT
# ─────────────────────────────────────────────
async def main():
    

    # Create MCP client with multiple servers
    client = MultiServerMCPClient(SERVERS)

    # Fetch all tools exposed by all MCP servers
    # This performs MCP handshake + tool discovery
    tools = await client.get_tools()

    # Create a lookup map: tool_name → tool_object
    # Makes tool execution easier later
    named_tools = {}
    for tool in tools:
        named_tools[tool.name] = tool

    print("Available tools:", named_tools.keys())

    # Initialize OpenAI LLM
    # This model will decide whether to call MCP tools
    llm = ChatOpenAI(model="gpt-4.1-nano")

    # (Optional alternative LLM – commented out)
    # llm = ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash-lite",
    #     temperature=0
    # )

    # Bind MCP tools to the LLM
    # tool_choice="auto" lets the model decide when to call tools
    llm_with_tools = llm.bind_tools(tools, tool_choice="auto")
    
    # ─────────────────────────────────────────
    # USER PROMPT
    # ─────────────────────────────────────────
    # Examples you can try:
    # prompt = "What is the product of 45 and 34?"
    # prompt = "What is the Captial of India"
    # prompt = "What is the remainder of 233 divided by 7?"
    prompt = "Add an expense - Rs 900 for groceries on 7th December"
    # prompt = "List all expenses in the December month"

    # First LLM invocation
    # The model may or may not return tool_calls
    response = await llm_with_tools.ainvoke(prompt)


    # If the model does NOT request any tools,
    # we directly print the response and exit
    if not getattr(response, "tool_calls", None):
        print("\nLLM Reply:", response.content)
        return

    # ─────────────────────────────────────────
    # TOOL EXECUTION PHASE
    # ─────────────────────────────────────────
    tool_messages = []

    # Iterate over all tool calls requested by the model
    for tc in response.tool_calls:
        selected_tool = tc["name"]
        selected_tool_args = tc.get("args") or {}
        selected_tool_id = tc["id"]

       # Execute the selected MCP tool
        result = await named_tools[selected_tool].ainvoke(selected_tool_args)

        # Wrap tool output in ToolMessage
        # tool_call_id is REQUIRED so the LLM can associate output
        tool_messages.append(ToolMessage(tool_call_id=selected_tool_id, content=json.dumps(result)))

    # ─────────────────────────────────────────
    # FINAL RESPONSE (LLM + TOOL OUTPUTS)
    # ─────────────────────────────────────────
    # We now call the LLM again with:
    # 1. Original user prompt
    # 2. Assistant message that requested tools
    # 3. Tool outputs
    final_response = await llm_with_tools.ainvoke(
        [
            HumanMessage(content=prompt),
            response,
            *tool_messages
        ]
    )
    print(f"Final response: {final_response.content}")

# ─────────────────────────────────────────────
# SCRIPT ENTRYPOINT
# ─────────────────────────────────────────────
if __name__ == '__main__':
    asyncio.run(main())
