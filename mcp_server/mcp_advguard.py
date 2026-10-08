import sys
import subprocess
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AdvGuard MCP Server")

@mcp.tool()
def analyze_transaction(csv_path: str) -> str:
    """
    Runs the AdvGuard C++ Data Structures Engine on a suspect transaction CSV.
    The C++ engine performs KD-Tree and LSH geometric checks to mathematically
    override vulnerable Python ML models.
    
    Returns the geometric forensic report.
    """
    # Assuming we run this from the project root or mcp_server dir
    engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../cpp_engine/build/advguard_engine"))
    
    if not os.path.exists(engine_path):
        # On Windows, the executable might have a .exe extension
        engine_path += ".exe"
        if not os.path.exists(engine_path):
            return "C++ engine executable not found. Please compile it in cpp_engine/build first."

    try:
        # Run the compiled C++ executable
        result = subprocess.run(
            [engine_path, csv_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing C++ engine: {e.stderr}\n{e.stdout}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    print("Starting AdvGuard MCP Server. You can connect a local LLM to query the `analyze_transaction` tool.")
    mcp.run()
