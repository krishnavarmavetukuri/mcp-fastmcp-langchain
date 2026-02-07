# MCP FastMCP LangChain Integration

This repository demonstrates a FastMCP-based client-server setup with LangChain integration. It includes:

- A **local math MCP server** (`servers/math-mcp-server`) exposing arithmetic tools.
- An **Expense Tracker MCP client** (`clients/expense-client`) that can interact with both local and remote MCP servers.
- A **Streamlit chatbot** that communicates with the MCP servers and an LLM to perform tasks and answer queries.

---

## Folder Structure

mcp-fastmcp-langchain/
├── clients/
│ └── expense-client/
│ ├── clientTesting.py # MCP client test script
│ ├── mcpClientChatBot.py # Streamlit chatbot
│ └── .env # API key placeholder (YOUR_API_KEY)
├── servers/
│ └── math-mcp-server/
│ └── main.py # Local MCP server
├── uv.toml # Unified dependencies
└── .gitignore



---

## Setup Instructions

### 1. Initialize UV environment

**Open a terminal in the root folder (`mcp-fastmcp-langchain`) and run:**

```
uv init .
uv add fastmcp langchain-mcp-adapters python-dotenv streamlit langchain-core langchain-openai langchain-google-genai google-generativeai
```


### 2. Run the Local MCP Server (Math)

Test if the local math server is working:

```
uv run fastmcp dev servers/math-mcp-server/main.py
```
This will start the MCP server locally and expose arithmetic tools.


### 3. Test Client Connection

Run the client testing script to ensure connections to both local and remote MCP servers are working:

```
python clients/expense-client/clientTesting.py
```

- The script connects to the local math server via stdio.
- It connects to the remote FastMCP Cloud server (Expense Tracker) via HTTP using **FAST_MCP_API_KEY**.

Make sure you replace **YOUR_API_KEY** in **.env** with your actual FastMCP API key.



###  4. Run the Streamlit Chatbot

Launch the chatbot application:

```
uv run streamlit run clients/expense-client/mcpClientChatBot.py
```

- This starts a web-based chat UI.
- The chatbot can handle both normal LLM queries and requests that require calling MCP tools.
- The chatbot communicates with:

    - Local math MCP server
    - Remote Expense Tracker MCP server

Open the URL shown in the terminal (usually http://localhost:8501) to interact with the chatbot.



## Notes

- **.env** contains only a placeholder key (**YOUR_API_KEY**) for security. Replace it with your actual key before running.
- All dependencies are managed via **UV** in the root **uv.toml**. There is no need to create separate virtual environments for clients or servers.
- Ensure that the **local MCP server** is running before testing client scripts or the chatbot.



## Dependencies

- fastmcp
- langchain-mcp-adapters
- langchain-core
- langchain-openai
- langchain-google-genai
- google-generativeai
- python-dotenv
- streamlit



All of these are installed automatically via:

```
uv add fastmcp langchain-mcp-adapters python-dotenv streamlit langchain-core langchain-openai langchain-google-genai google-generativeai
```

## Author
Krishna Varma Vetukuri



















