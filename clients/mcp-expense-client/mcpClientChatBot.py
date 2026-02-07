# ─────────────────────────────────────────────
# MCP + Streamlit Chat Application
# This app connects an LLM to multiple MCP servers
# and exposes them through a chat UI
# ─────────────────────────────────────────────

import os
import json
import asyncio
import streamlit as st
from dotenv import load_dotenv

# LangChain + MCP imports
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage
)

# Load environment variables (.env)
load_dotenv()

# FastMCP Cloud API key used for remote MCP authentication
FAST_MCP_API_KEY = os.getenv("FAST_MCP_API_KEY")


# ─────────────────────────────────────────────
# MCP SERVER DEFINITIONS
# ─────────────────────────────────────────────
# We connect to:
# 1. A LOCAL MCP server (math) via stdio
# 2. A REMOTE FastMCP Cloud server (expense) via HTTP
SERVERS = { 
    "math": {
        # Local MCP server launched as a subprocess
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
        "transport": "streamable_http",
        "url": "https://simple-addition.fastmcp.app/mcp",
        # Bearer token authentication
        "headers": {
            "Authorization": f"Bearer {FAST_MCP_API_KEY}"
        }
    }
}

# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You have access to tools. When you choose to call a tool, do not narrate status updates. "
    "After tools run, return only a concise final answer."
)

# ─────────────────────────────────────────────
# STREAMLIT UI SETUP
# ─────────────────────────────────────────────
st.set_page_config(page_title="MCP Chat", layout="centered")
st.title("MCP Chat Bot")

# ─────────────────────────────────────────────
# ONE-TIME INITIALIZATION (SESSION STATE)
# ─────────────────────────────────────────────
# This block runs only once per Streamlit session
if "initialized" not in st.session_state:
    # 1) Initialize the LLM
    st.session_state.llm = ChatOpenAI(model="gpt-4.1-nano")

    # 2) Create MCP client and fetch tools
    # This performs:
    # - MCP handshake
    # - Tool discovery from all configured servers
    st.session_state.client = MultiServerMCPClient(SERVERS)
    tools = asyncio.run(st.session_state.client.get_tools())

    # Store tools and create name -> tool lookup
    st.session_state.tools = tools
    st.session_state.tool_by_name = {t.name: t for t in tools}

    # 3) Bind tools to the LLM
    # This allows the LLM to emit tool_calls
    st.session_state.llm_with_tools = st.session_state.llm.bind_tools(tools)

    # 4) Initialize conversation history
    # SystemMessage must always come first
    st.session_state.history = [SystemMessage(content=SYSTEM_PROMPT)]
    st.session_state.initialized = True


# ─────────────────────────────────────────────
# RENDER CHAT HISTORY
# ─────────────────────────────────────────────
# We render:
# - Human messages
# - Final AI messages
# We DO NOT render:
# - System messages
# - Tool messages
# - Intermediate AI messages with tool_calls
for msg in st.session_state.history:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        # Skip intermediate assistant messages that requested tools
        if getattr(msg, "tool_calls", None):
            continue
        with st.chat_message("assistant"):
            st.markdown(msg.content)
    # ToolMessage and SystemMessage are intentionally hidden


# ─────────────────────────────────────────────
# CHAT INPUT HANDLING
# ─────────────────────────────────────────────
user_text = st.chat_input("Type a message…")
if user_text:
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_text)

    # Append user message to conversation history
    st.session_state.history.append(HumanMessage(content=user_text))

    # ─────────────────────────────────────────
    # FIRST LLM INVOCATION
    # ─────────────────────────────────────────
    # The LLM decides whether tools are needed
    first = asyncio.run(st.session_state.llm_with_tools.ainvoke(st.session_state.history))
    tool_calls = getattr(first, "tool_calls", None)

    # ─────────────────────────────────────────
    # CASE 1: NO TOOLS REQUIRED
    # ─────────────────────────────────────────
    if not tool_calls:
        with st.chat_message("assistant"):
            st.markdown(first.content or "")
        st.session_state.history.append(first)

    # ─────────────────────────────────────────
    # CASE 2: TOOLS REQUIRED
    # ─────────────────────────────────────────
    else:
        # 1) Append assistant message with tool_calls (not rendered)
        st.session_state.history.append(first)

        # 2) Execute each requested MCP tool
        tool_msgs = []
        for tc in tool_calls:
            name = tc["name"]
            args = tc.get("args") or {}

            # Handle cases where args arrive as JSON string
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass

            # Invoke the corresponding MCP tool
            tool = st.session_state.tool_by_name[name]
            res = asyncio.run(tool.ainvoke(args))

            # Wrap tool output in ToolMessage
            tool_msgs.append(ToolMessage(tool_call_id=tc["id"], content=json.dumps(res)))

        # Append all tool outputs to history
        st.session_state.history.extend(tool_msgs)

        # 3) FINAL LLM INVOCATION
        # The LLM now sees tool results and produces final answer
        final = asyncio.run(st.session_state.llm.ainvoke(st.session_state.history))
        
        with st.chat_message("assistant"):
            st.markdown(final.content or "")

        # Store final assistant message
        st.session_state.history.append(AIMessage(content=final.content or ""))