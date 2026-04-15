import sys
import os
os.environ["SERPAPI_API_KEY"] = os.environ.get("SERPAPI_API_KEY", "")
import src.server
src.server.mcp.run(transport="stdio", show_banner=False)
