from __future__ import annotations

# FastMCP is a lightweight framework for building MCP-compatible tool servers
from fastmcp import FastMCP

# ─────────────────────────────────────────────
# MCP SERVER INITIALIZATION
# ─────────────────────────────────────────────
# Create a FastMCP server instance.
# "arith" is the server name that will be visible to MCP clients.
mcp = FastMCP("arith")

# ─────────────────────────────────────────────
# HELPER FUNCTION
# ─────────────────────────────────────────────
def _as_number(x):
    """
    Safely convert input into a numeric value.

    Accepts:
    - int
    - float
    - numeric strings (e.g., "12", "3.14")

    Raises:
    - TypeError if the input cannot be converted to a number

    This makes the tools more robust when called by LLMs,
    which may pass values as strings.
    """
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        return float(x.strip())
    raise TypeError("Expected a number (int/float or numeric string)")


# ─────────────────────────────────────────────
# MCP TOOLS (EXPOSED FUNCTIONS)
# ─────────────────────────────────────────────
# Each function decorated with @mcp.tool()
# becomes an MCP tool that can be discovered and
# invoked by MCP-compatible clients (LangChain, etc.)
@mcp.tool()
async def add(a: float, b: float) -> float:
    """
    Add two numbers and return the result.
    """
    return _as_number(a) + _as_number(b)

@mcp.tool()
async def subtract(a: float, b: float) -> float:
    """
    Subtract b from a and return the result.
    """
    return _as_number(a) - _as_number(b)

@mcp.tool()
async def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers and return the result.
    """
    return _as_number(a) * _as_number(b)

@mcp.tool()
async def divide(a: float, b: float) -> float:
    """
    Divide a by b and return the result.

    Raises:
    - ValueError if b is zero
    """
    divisor = _as_number(b)
    if divisor == 0:
        raise ValueError("Cannot divide by zero")
    return _as_number(a) / divisor

@mcp.tool()
async def power(a: float, b: float) -> float:
    """
    Raise a to the power of b and return the result.
    """
    return _as_number(a) ** _as_number(b)

@mcp.tool()
async def modulus(a: float, b: float) -> float:
    """
    Return the remainder when a is divided by b.

    Raises:
    - ValueError if b is zero
    """
    divisor = _as_number(b)
    if divisor == 0:
        raise ValueError("Cannot perform modulus by zero")
    return _as_number(a) % divisor

# ─────────────────────────────────────────────
# SERVER ENTRYPOINT
# ─────────────────────────────────────────────
# This block is executed when the file is run directly.
# Example:
#   uv run fastmcp run main.py
#
# It starts the MCP server and waits for tool calls
# from MCP clients via stdio or HTTP transport.
if __name__ == "__main__":
    mcp.run()
