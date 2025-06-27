#!/usr/bin/env python3
"""
Radio Streamer API - Main entry point

This is a simple entry point that imports the FastAPI app from api.py
and runs it using uvicorn.
"""

import uvicorn
from api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
