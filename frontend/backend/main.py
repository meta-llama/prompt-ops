"""
FastAPI application setup and configuration.
"""

import importlib
import logging
import os
import subprocess
import sys
from typing import Any, Dict

# Import configuration and utilities
from config import (
    BACKEND_HOST,
    BACKEND_PORT,
    DATASET_ADAPTER_MAPPING,
    DEBUG_MODE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TRAIN_SIZE,
    DEFAULT_VAL_SIZE,
    FAIL_ON_ERROR,
    METRIC_MAPPING,
    MODEL_MAPPING,
    STRATEGY_MAPPING,
)
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

# Import route modules
from routes import datasets, projects, prompts, websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("backend.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Check for WebSocket support
try:
    import websockets as websockets_lib

    print("✓ WebSocket support is available")
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    print("⚠️  WARNING: WebSocket support not available!")
    print("   Install with: pip install websockets")
    print("   WebSocket endpoints will not work until this is installed.")
    WEBSOCKETS_AVAILABLE = False

# Install required dependencies if missing
required_packages = ["scipy", "llama-prompt-ops==0.0.7"]
try:
    for package in required_packages:
        try:
            # Handle special case for llama-prompt-ops
            if "llama-prompt-ops" in package:
                module_name = "llama_prompt_ops"
            else:
                module_name = package.replace("-", "_")

            importlib.import_module(module_name)
            print(f"✓ {package} is already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} installed successfully")
except Exception as e:
    print(f"Warning: Failed to install dependencies: {e}")

# Add llama-prompt-ops to Python path
llama_prompt_ops_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "src")
)
if llama_prompt_ops_path not in sys.path:
    sys.path.insert(0, llama_prompt_ops_path)
    print(f"Added {llama_prompt_ops_path} to Python path")

# Try to import core modules
try:
    from llama_prompt_ops.core.migrator import PromptMigrator

    print("✓ Successfully imported llama_prompt_ops core modules")
    LLAMA_PROMPT_OPS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import llama_prompt_ops: {e}")
    print("The /api/migrate-prompt endpoint will fall back to OpenRouter")
    LLAMA_PROMPT_OPS_AVAILABLE = False

# FastAPI Application Setup
app = FastAPI(title="Llama Prompt Ops API")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(datasets.router)
app.include_router(prompts.router)
app.include_router(projects.router)
app.include_router(websockets.router)


# Pydantic models for remaining endpoints
class ConfigResponse(BaseModel):
    models: Dict[str, str]
    metrics: Dict[str, Dict]
    dataset_adapters: Dict[str, Dict]
    strategies: Dict[str, str]


# Remaining endpoints that don't fit in other modules
@app.options("/api/enhance-prompt")
@app.options("/api/migrate-prompt")
@app.options("/api/configurations")
@app.options("/api/settings")
@app.options("/api/datasets/upload")
@app.options("/api/datasets")
@app.options("/api/datasets/{filename}")
@app.options("/api/datasets/analyze/{filename}")
@app.options("/api/datasets/preview-transformation")
@app.options("/api/datasets/save-mapping")
@app.options("/api/quick-start-demo")
@app.options("/api/docs/structure")
@app.options("/docs/{file_path:path}")
async def options_route():
    return {"status": "OK"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify backend dependencies."""
    issues = []

    if not WEBSOCKETS_AVAILABLE:
        issues.append(
            {
                "component": "websockets",
                "status": "missing",
                "message": "WebSocket support not available. Install with: pip install websockets",
                "severity": "error",
            }
        )

    if not LLAMA_PROMPT_OPS_AVAILABLE:
        issues.append(
            {
                "component": "llama-prompt-ops",
                "status": "missing",
                "message": "llama-prompt-ops not available. Some features may not work.",
                "severity": "warning",
            }
        )

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        issues.append(
            {
                "component": "api_key",
                "status": "missing",
                "message": "OPENROUTER_API_KEY not set in environment",
                "severity": "warning",
            }
        )

    return {
        "status": "healthy" if len(issues) == 0 else "degraded",
        "websockets_available": WEBSOCKETS_AVAILABLE,
        "llama_prompt_ops_available": LLAMA_PROMPT_OPS_AVAILABLE,
        "api_key_configured": bool(api_key),
        "issues": issues,
    }


@app.get("/api/settings")
async def get_settings():
    """Return current environment-configurable settings."""
    return {
        "failOnError": FAIL_ON_ERROR,
        "debugMode": DEBUG_MODE,
        "defaultModel": DEFAULT_MODEL,
        "defaultTemperature": DEFAULT_TEMPERATURE,
        "defaultTrainSize": DEFAULT_TRAIN_SIZE,
        "defaultValSize": DEFAULT_VAL_SIZE,
        "hasOpenRouterKey": bool(os.getenv("OPENROUTER_API_KEY")),
        "hasTogetherKey": bool(os.getenv("TOGETHER_API_KEY")),
    }


@app.get("/api/configurations", response_model=ConfigResponse)
async def get_configurations():
    """Return available configuration options for the frontend."""
    return {
        "models": MODEL_MAPPING,
        "metrics": METRIC_MAPPING,
        "dataset_adapters": DATASET_ADAPTER_MAPPING,
        "strategies": STRATEGY_MAPPING,
    }


@app.get("/docs/{file_path:path}")
async def get_docs_file(file_path: str):
    """Serve documentation files from the docs directory."""
    try:
        # Construct the path to the docs file
        docs_base_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs")
        full_path = os.path.join(docs_base_path, file_path)

        # Security check: ensure the path is within the docs directory
        real_docs_path = os.path.realpath(docs_base_path)
        real_file_path = os.path.realpath(full_path)
        if not real_file_path.startswith(real_docs_path):
            raise HTTPException(status_code=403, detail="Access denied")

        # Check if file exists
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Documentation file not found")

        # Read and return the file content
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Return appropriate content type based on file extension
        if file_path.endswith(".md"):
            return PlainTextResponse(content, media_type="text/markdown")
        elif file_path.endswith(".json"):
            return PlainTextResponse(content, media_type="application/json")
        else:
            return PlainTextResponse(content, media_type="text/plain")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading documentation file: {str(e)}"
        )


@app.get("/api/docs/structure")
async def get_docs_structure():
    """Get the structure of the documentation directory."""
    try:
        docs_base_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs")
        structure = []

        def scan_directory(path, relative_path=""):
            items = []
            if not os.path.exists(path):
                return items

            for item in os.listdir(path):
                if item.startswith("."):  # Skip hidden files
                    continue

                item_path = os.path.join(path, item)
                item_relative_path = (
                    os.path.join(relative_path, item) if relative_path else item
                )

                if os.path.isdir(item_path):
                    # Recursively scan subdirectories
                    subitems = scan_directory(item_path, item_relative_path)
                    items.extend(subitems)
                elif item.endswith((".md", ".txt")):
                    # Get file stats
                    stat = os.stat(item_path)
                    items.append(
                        {
                            "path": item_relative_path.replace(os.sep, "/"),
                            "name": os.path.splitext(item)[0],
                            "type": "file",
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                        }
                    )

            return items

        structure = scan_directory(docs_base_path)

        return {"success": True, "structure": structure, "total_files": len(structure)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error scanning docs directory: {str(e)}"
        )


# Main
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)
