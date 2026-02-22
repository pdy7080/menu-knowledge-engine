"""
Test server to verify matching engine
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("Starting test server on port 8002...")
    print("Available routes:")
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            print(f"  {route.methods} {route.path}")

    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")
