"""
FastAPI application setup and configuration.
"""

import importlib
import logging
import os
import re
import subprocess
import sys
from typing import Any, Dict, Optional

import yaml

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

    logger.info("WebSocket support is available")
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    logger.warning("WebSocket support not available!")
    logger.warning("Install with: pip install websockets")
    logger.warning("WebSocket endpoints will not work until this is installed.")
    WEBSOCKETS_AVAILABLE = False

# Check for required dependencies
# Note: prompt-ops should be installed via 'pip install -e .' from the repo root
required_packages = ["scipy", "prompt_ops"]
for package in required_packages:
    try:
        importlib.import_module(package)
        logger.info(f"✓ {package} is available")
    except ImportError:
        if package == "prompt_ops":
            logger.warning(
                f"⚠ {package} not found. Install it with: pip install -e . (from repo root)"
            )
        else:
            logger.warning(
                f"⚠ {package} not found. Install it with: pip install {package}"
            )

# Add prompt-ops to Python path
prompt_ops_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "src")
)
if prompt_ops_path not in sys.path:
    sys.path.insert(0, prompt_ops_path)
    logger.info(f"Added {prompt_ops_path} to Python path")

# Import shared core module with availability checks
from core import PROMPT_OPS_AVAILABLE

# FastAPI Application Setup
app = FastAPI(title="Prompt Ops API")

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

    if not PROMPT_OPS_AVAILABLE:
        issues.append(
            {
                "component": "prompt-ops",
                "status": "missing",
                "message": "prompt-ops not available. Some features may not work.",
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
        "prompt_ops_available": PROMPT_OPS_AVAILABLE,
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


def parse_frontmatter(content: str) -> tuple[Optional[Dict[str, Any]], str]:
    """
    Parse YAML frontmatter from markdown content.
    Returns (frontmatter_dict, remaining_content) or (None, original_content) if no frontmatter.
    """
    frontmatter_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = frontmatter_pattern.match(content)

    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1))
            remaining_content = content[match.end() :]
            return frontmatter, remaining_content
        except yaml.YAMLError:
            return None, content

    return None, content


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

        # Strip frontmatter from markdown files before serving
        if file_path.endswith(".md"):
            _, content = parse_frontmatter(content)
            return PlainTextResponse(content, media_type="text/markdown")
        elif file_path.endswith(".json"):
            return PlainTextResponse(content, media_type="application/json")
        else:
            return PlainTextResponse(content, media_type="text/plain")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading documentation file: {str(e)}"
        )


def generate_doc_id(path: str) -> str:
    """Generate a URL-friendly ID from a file path."""
    # Remove extension and convert path separators to dashes
    doc_id = os.path.splitext(path)[0].replace("/", "-").replace("\\", "-").lower()
    # Clean up any double dashes and leading/trailing dashes
    doc_id = re.sub(r"-+", "-", doc_id).strip("-")
    return doc_id


@app.get("/api/docs/structure")
async def get_docs_structure():
    """Get the structure of the documentation directory with frontmatter metadata."""
    try:
        docs_base_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs")
        docs = []

        def scan_directory(path, relative_path=""):
            items = []
            if not os.path.exists(path):
                return items

            for item in os.listdir(path):
                if item.startswith(".") or item.startswith("_"):  # Skip hidden/private
                    continue

                item_path = os.path.join(path, item)
                item_relative_path = (
                    os.path.join(relative_path, item) if relative_path else item
                )

                if os.path.isdir(item_path):
                    # Recursively scan subdirectories
                    subitems = scan_directory(item_path, item_relative_path)
                    items.extend(subitems)
                elif item.endswith(".md"):
                    # Read file and parse frontmatter
                    try:
                        with open(item_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        frontmatter, _ = parse_frontmatter(content)
                        file_path = item_relative_path.replace(os.sep, "/")

                        # Build doc entry with frontmatter metadata or defaults
                        doc_entry = {
                            "id": generate_doc_id(file_path),
                            "path": file_path,
                            "title": (
                                frontmatter.get("title")
                                if frontmatter
                                else os.path.splitext(item)[0]
                                .replace("-", " ")
                                .replace("_", " ")
                                .title()
                            ),
                            "category": (
                                frontmatter.get("category")
                                if frontmatter
                                else relative_path.replace(os.sep, "/").title()
                                or "General"
                            ),
                            "description": (
                                frontmatter.get("description") if frontmatter else None
                            ),
                            "order": (
                                frontmatter.get("order") if frontmatter else 999
                            ),
                            "icon": frontmatter.get("icon") if frontmatter else None,
                        }
                        items.append(doc_entry)
                    except Exception as e:
                        logger.warning(f"Failed to parse doc file {item_path}: {e}")
                        continue

            return items

        docs = scan_directory(docs_base_path)

        # Sort by order, then by title
        docs.sort(key=lambda x: (x.get("order", 999), x.get("title", "")))

        return {"success": True, "docs": docs, "total": len(docs)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error scanning docs directory: {str(e)}"
        )


# Main
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)
