"""Entry point for the MCP SSH session server."""
import os

# Load environment variables from SSH_ENV_FILE if specified
env_file = os.getenv("SSH_ENV_FILE")
if env_file:
    from dotenv import load_dotenv
    load_dotenv(env_file, override=True)

from .server import mcp


def main():
    """Main entry point for the MCP SSH session server."""
    # Run in SSE mode if SSE_PORT is set, otherwise stdio
    sse_port = os.getenv("SSE_PORT")
    if sse_port:
        mcp.run(transport="sse", host="0.0.0.0", port=int(sse_port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
