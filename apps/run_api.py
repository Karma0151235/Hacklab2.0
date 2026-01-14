"""
Run the FastAPI server
"""

import sys
import asyncio
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Disabled for Windows + Playwright compatibility
        log_level="info"
    )
