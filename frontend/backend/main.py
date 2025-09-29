import asyncio
import importlib
import importlib.util
import json
import logging
import os
import shutil
import subprocess
import sys
import traceback
from typing import Any, Dict, List, Optional

import openai
import yaml

# Import config transformer
from config_transformer import ConfigurationTransformer

# Import dataset analyzer
from dataset_analyzer import DatasetAnalyzer
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("backend.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize dataset analyzer
dataset_analyzer = DatasetAnalyzer()

# --- Environment and Path Setup ---

# Load environment variables from .env file
load_dotenv()

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
    # Continue execution - we'll handle missing dependencies gracefully

# Add llama-prompt-ops to Python path
llama_prompt_ops_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "src")
)
if llama_prompt_ops_path not in sys.path:
    sys.path.insert(0, llama_prompt_ops_path)
    print(f"Added {llama_prompt_ops_path} to Python path")

# Try to import core modules - but don't exit on failure
# We'll handle import errors gracefully in the endpoints
try:
    from llama_prompt_ops.core.migrator import PromptMigrator

    print("✓ Successfully imported llama_prompt_ops core modules")
    LLAMA_PROMPT_OPS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import llama_prompt_ops: {e}")
    print(f"Attempted to add to path: {llama_prompt_ops_path}")
    print("The /api/migrate-prompt endpoint will fall back to OpenRouter")
    LLAMA_PROMPT_OPS_AVAILABLE = False

# --- Core Library Imports (deferred until path is set) ---
# Import llama-prompt-ops modules only if available
if LLAMA_PROMPT_OPS_AVAILABLE:
    try:
        from llama_prompt_ops.core.datasets import ConfigurableJSONAdapter
        from llama_prompt_ops.core.metrics import DSPyMetricAdapter
        from llama_prompt_ops.core.model import setup_model
        from llama_prompt_ops.core.model_strategies import LlamaStrategy

        print("✓ Successfully imported all required llama_prompt_ops modules")
    except ImportError as e:
        print(f"Warning: Failed to import some llama_prompt_ops modules: {e}")
        LLAMA_PROMPT_OPS_AVAILABLE = False

# --- FastAPI Application Setup ---
app = FastAPI(title="Llama Prompt Ops API")

# CORS for local development; tighten in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Check for OpenRouter API key in environment
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_api_key:
    print(
        "Warning: OPENROUTER_API_KEY not found in environment variables. Will try to use key from frontend."
    )

# Initialize OpenRouter client using OpenAI SDK (OpenRouter is OpenAI-compatible)
client = openai.OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)

# --- Configuration Mappings ------------------------------------------

# Available models (these would be configured based on your available models)
MODEL_MAPPING = {
    "Llama 3.3 70B": "meta-llama/llama-3.3-70b-instruct",
    "Llama 3.1 8B": "meta-llama/llama-3.1-8b-instruct",
    "Llama 3.1 70B": "meta-llama/llama-3.1-70b-instruct",
    "GPT-4o": "openai/gpt-4o",
    "GPT-4o-mini": "openai/gpt-4o-mini",
}

# Available metrics from llama-prompt-ops
METRIC_MAPPING = {
    "exact_match": {
        "class": "llama_prompt_ops.core.metrics.ExactMatchMetric",
        "params": {"output_field": "answer"},
    },
    "semantic_similarity": {
        "class": "llama_prompt_ops.core.metrics.DSPyMetricAdapter",
        "params": {
            "signature_name": "similarity",
            "score_range": (1, 10),
            "normalize_to": (0, 1),
        },
    },
    "correctness": {
        "class": "llama_prompt_ops.core.metrics.DSPyMetricAdapter",
        "params": {
            "signature_name": "correctness",
            "score_range": (1, 10),
            "normalize_to": (0, 1),
        },
    },
    "json_structured": {
        "class": "llama_prompt_ops.core.metrics.StandardJSONMetric",
        "params": {
            "output_field": "answer",
            "evaluation_mode": "selected_fields_comparison",
            "strict_json": False,
        },
    },
    # Legacy mappings for backward compatibility
    "Facility Support": {
        "class": "llama_prompt_ops.core.metrics.FacilityMetric",
        "params": {"output_field": "answer"},
    },
    "HotpotQA": {
        "class": "llama_prompt_ops.datasets.hotpotqa.HotpotQAMetric",
        "params": {"output_field": "answer"},
    },
    "Standard JSON": {
        "class": "llama_prompt_ops.core.metrics.StandardJSONMetric",
        "params": {"output_field": "answer"},
    },
    "Exact Match": {
        "class": "llama_prompt_ops.core.metrics.ExactMatchMetric",
        "params": {},
    },
}

# Available dataset adapters from llama-prompt-ops
DATASET_ADAPTER_MAPPING = {
    "standard_json": {
        "adapter_class": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
        "description": "Standard JSON format with customizable field mappings",
        "example_fields": {"input": "string", "output": "string"},
        "params": {"input_field": "input", "golden_output_field": "output"},
    },
    "hotpotqa": {
        "adapter_class": "llama_prompt_ops.datasets.hotpotqa.adapter.HotPotQAAdapter",
        "description": "Multi-hop reasoning dataset for question answering",
        "example_fields": {
            "question": "string",
            "answer": "string",
            "context": "array",
        },
        "params": {
            "input_field": "question",
            "golden_output_field": "answer",
            "context_field": "context",
        },
    },
    "facility": {
        "adapter_class": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
        "description": "Facility support and maintenance dataset with nested field structure",
        "example_fields": {"fields": "object", "answer": "string"},
        "params": {
            # Nested path for facility dataset
            "input_field": ["fields", "input"],
            "golden_output_field": "answer",
        },
    },
}

# Available optimization strategies from llama-prompt-ops
STRATEGY_MAPPING = {
    "Basic": "basic",
}

# --- Pydantic Models -----------------------------------------------------


class PromptRequest(BaseModel):
    prompt: str
    config: Optional[Dict[str, Any]] = None


class PromptResponse(BaseModel):
    optimizedPrompt: str


class ConfigResponse(BaseModel):
    models: Dict[str, str]
    metrics: Dict[str, Dict]
    # Changed from datasets to dataset_adapters
    dataset_adapters: Dict[str, Dict]
    strategies: Dict[str, str]


class DatasetUploadResponse(BaseModel):
    filename: str
    path: str
    preview: List[Dict[str, Any]]
    total_records: int


class DatasetListResponse(BaseModel):
    datasets: List[Dict[str, Any]]


class QuickStartResponse(BaseModel):
    success: bool
    dataset: DatasetUploadResponse
    prompt: str
    config: Dict[str, Any]
    message: str


# Dataset analysis models
class DatasetAnalysisResponse(BaseModel):
    total_records: int
    sample_size: int
    fields: List[Dict[str, Any]]
    suggestions: Dict[str, Any]
    sample_data: List[Dict[str, Any]]
    error: Optional[str] = None


class FieldMappingRequest(BaseModel):
    filename: str
    mappings: Dict[str, str]
    use_case: str


class PreviewTransformationRequest(BaseModel):
    filename: str
    mappings: Dict[str, str]
    use_case: str


class PreviewTransformationResponse(BaseModel):
    original_data: List[Dict[str, Any]]
    transformed_data: List[Dict[str, Any]]
    adapter_config: Dict[str, Any]
    error: Optional[str] = None


# --- System Messages for OpenRouter Operations ---

ENHANCE_SYSTEM_MESSAGE = """
    You are a highly advanced language model, capable of complex reasoning and problem-solving.
    Your goal is to provide accurate and informative responses to the given input, following a    structured approach.
            Here is the input you'll work with:
            <INPUT>
            {{USER_INPUT}}
            </INPUT>
            To accomplish this, follow these steps:
            Understand the Task: Carefully read and comprehend the input, identifying the key elements and requirements.
            Break Down the Problem: Decompose the task into smaller, manageable sub-problems, using a chain-of-thought (CoT) approach.
            Gather Relevant Information: If necessary, use external knowledge sources to gather relevant information and provide provenance for your answers.
            Apply Reasoning and Logic: Apply step-by-step reasoning and logical thinking to arrive at a solution, using self-ask prompting to guide your thought process.
            Evaluate and Refine: Evaluate your solution, refining it as needed to ensure accuracy and completeness.
            Your output must follow these guidelines:
            Clear and Concise: Provide clear and concise responses, avoiding ambiguity and jargon.
            Well-Structured: Use a well-structured format for your response, including headings and bullet points as needed.
            Accurate and Informative: Ensure that your response is accurate and informative, providing relevant details and examples.
            Format your final answer inside <OUTPUT> tags and do not include any of your internal reasoning.
            <OUTPUT>
            ...your response...
            </OUTPUT>
            Chain of Thought (CoT) Template
            To facilitate CoT, use the following template:
            Step 1: Identify the key elements and requirements of the task.
            Sub-question: What are the essential components of the task?
            Answer: [Provide a brief answer]
            Step 2: Break down the problem into smaller sub-problems.
            Sub-question: How can I decompose the task into manageable parts?
            Answer: [Provide a brief answer]
            Step 3: Gather relevant information and apply reasoning and logic.
            Sub-question: What information do I need to solve the task, and how can I apply logical thinking?
            Answer: [Provide a brief answer]
            Step 4: Evaluate and refine the solution.
            Sub-question: Is my solution accurate and complete, and how can I refine it?
            Answer: [Provide a brief answer]
            By following this structured approach, you will be able to provide accurate and informative responses to the given input, demonstrating your ability to think critically and solve complex problems."""
# --- Utility -------------------------------------------------------------


def load_class_dynamically(class_path: str):
    """Import and return class from dotted path string."""
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def create_openrouter_client(api_key: str = None):
    """Create OpenRouter client with the provided API key."""
    key_to_use = api_key or openrouter_api_key
    if not key_to_use:
        raise ValueError("OpenRouter API key is required")

    return openai.OpenAI(
        api_key=key_to_use,
        base_url="https://openrouter.ai/api/v1",
    )


async def enhance_prompt_with_openrouter(
    request: PromptRequest, system_message: str, operation_name: str = "processing"
):
    """
    Shared function to enhance prompts using OpenRouter.

    Args:
        request: The prompt request containing prompt and config
        system_message: The system message to use for the operation
        operation_name: Name of the operation for error messages

    Returns:
        PromptResponse with the enhanced prompt
    """
    config = request.config or {}

    # API key precedence: env > client supplied
    api_key = openrouter_api_key or config.get("openrouterApiKey")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="OpenRouter API key missing. Supply via UI or set OPENROUTER_API_KEY environment variable.",
        )

    try:
        # Create OpenRouter client with the API key
        openrouter_client = create_openrouter_client(api_key)

        # Use the model from config or default to Llama 3.3 70B
        model = config.get("model", "meta-llama/llama-3.3-70b-instruct")
        if model in MODEL_MAPPING:
            model = MODEL_MAPPING[model]

        response = openrouter_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": request.prompt},
            ],
            temperature=0.7,
        )

        enhanced_prompt = response.choices[0].message.content.strip()
        return {"optimizedPrompt": enhanced_prompt}

    except Exception as e:
        print(f"Error in {operation_name}: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error {operation_name} prompt: {str(e)}"
        )


# --- Dataset Storage -----------------------------------------------------

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploaded_datasets")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_uploaded_datasets():
    """Get list of uploaded datasets."""
    datasets = []
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(UPLOAD_DIR, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        # Get first few records for preview
                        preview = data[:3] if isinstance(data, list) else []
                        datasets.append(
                            {
                                "name": f"Uploaded: {filename}",
                                "filename": filename,
                                "path": filepath,
                                "preview": preview,
                                "total_records": (
                                    len(data) if isinstance(data, list) else 0
                                ),
                            }
                        )
                except Exception as e:
                    print(f"Error reading dataset {filename}: {e}")
    return datasets


def generate_unique_project_name(base_name: str, base_dir: str) -> str:
    """
    Generate a unique project name by adding incremental suffixes if the project already exists.

    Args:
        base_name: The desired project name (e.g., "qa-project-2025-09-15")
        base_dir: The directory where projects are created

    Returns:
        Unique project name (e.g., "qa-project-2025-09-15-2" if original exists)
    """
    project_path = os.path.join(base_dir, base_name)

    # If the base name doesn't exist, use it
    if not os.path.exists(project_path):
        return base_name

    # Otherwise, find the next available incremental name
    counter = 2
    while True:
        incremental_name = f"{base_name}-{counter}"
        incremental_path = os.path.join(base_dir, incremental_name)

        if not os.path.exists(incremental_path):
            return incremental_name

        counter += 1

        # Safety check to prevent infinite loop (though very unlikely)
        if counter > 1000:
            # Fallback to timestamp-based naming
            import time

            timestamp = str(int(time.time()))
            return f"{base_name}-{timestamp}"


# --- WebSocket Streaming Classes ----------------------------------------


class StreamingLogHandler(logging.Handler):
    """Custom log handler that streams log messages to WebSocket clients."""

    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket
        self.formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")

    def emit(self, record):
        """Send log record to WebSocket client."""
        try:
            log_entry = self.format(record)
            # Create task to send message (non-blocking)
            asyncio.create_task(
                self.websocket.send_json(
                    {
                        "type": "log",
                        "message": log_entry,
                        "level": record.levelname,
                        "logger": record.name,
                        "timestamp": record.created,
                    }
                )
            )
        except Exception as e:
            # Avoid infinite recursion by not logging this error
            pass


class OptimizationManager:
    """Manages the optimization process with real-time streaming."""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.log_handler = None

    async def send_status(self, message: str, phase: str = None):
        """Send status update to client."""
        await self.websocket.send_json(
            {"type": "status", "message": message, "phase": phase or "unknown"}
        )

    async def send_progress(self, phase: str, progress: float, message: str):
        """Send progress update to client."""
        await self.websocket.send_json(
            {
                "type": "progress",
                "phase": phase,
                "progress": progress,
                "message": message,
            }
        )

    async def send_result(self, result: dict):
        """Send final optimization result to client."""
        await self.websocket.send_json({"type": "complete", **result})

    async def send_error(self, error: str):
        """Send error message to client."""
        await self.websocket.send_json({"type": "error", "message": error})

    def setup_log_streaming(self):
        """Set up log handlers to capture all optimization logs."""
        self.log_handler = StreamingLogHandler(self.websocket)
        self.log_handler.setLevel(logging.INFO)

        # Add handler to multiple loggers to capture all output
        loggers_to_stream = [
            logging.getLogger(),  # Root logger
            logging.getLogger("prompt_ops"),  # llama-prompt-ops logger
            logging.getLogger("llama_prompt_ops"),  # Alternative logger name
            logging.getLogger("dspy"),  # DSPy optimization logs
            logging.getLogger("LiteLLM"),  # LiteLLM API call logs
        ]

        for logger in loggers_to_stream:
            logger.addHandler(self.log_handler)

    def cleanup_log_streaming(self):
        """Clean up log handlers."""
        if self.log_handler:
            loggers_to_cleanup = [
                logging.getLogger(),
                logging.getLogger("prompt_ops"),
                logging.getLogger("llama_prompt_ops"),
                logging.getLogger("dspy"),
                logging.getLogger("LiteLLM"),
            ]

            for logger in loggers_to_cleanup:
                try:
                    logger.removeHandler(self.log_handler)
                except ValueError:
                    # Handler not in logger, ignore
                    pass


# --- Routes --------------------------------------------------------------


@app.options("/api/enhance-prompt")
@app.options("/api/migrate-prompt")
@app.options("/api/configurations")
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


@app.get("/api/configurations", response_model=ConfigResponse)
async def get_configurations():
    """Return available configuration options for the frontend."""
    return {
        "models": MODEL_MAPPING,
        "metrics": METRIC_MAPPING,
        "dataset_adapters": DATASET_ADAPTER_MAPPING,  # Just return the adapter types
        "strategies": STRATEGY_MAPPING,
    }


@app.post("/api/datasets/upload", response_model=DatasetUploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a dataset file."""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    try:
        # Create the directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Get list of existing dataset files
        existing_files = os.listdir(UPLOAD_DIR)

        # Delete all existing dataset files to enforce one-dataset-at-a-time rule
        for existing_file in existing_files:
            file_path = os.path.join(UPLOAD_DIR, existing_file)
            if os.path.isfile(file_path) and existing_file.endswith(".json"):
                os.remove(file_path)
                logger.info(f"Deleted existing dataset: {existing_file}")

        # Read and validate JSON
        contents = await file.read()
        try:
            data = json.loads(contents)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in uploaded file {file.filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")

        # Validate that it's a list of objects
        if not isinstance(data, list):
            raise HTTPException(
                status_code=400, detail="Dataset must be a JSON array of objects"
            )

        if len(data) == 0:
            raise HTTPException(status_code=400, detail="Dataset cannot be empty")

        # Validate that each item is an object
        for i, item in enumerate(data[:5]):  # Check first 5 items
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=400, detail=f"Item {i+1} is not an object"
                )

        logger.info(f"Successfully validated dataset with {len(data)} records")

        # Save to disk
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        # Get preview
        preview = data[:5] if isinstance(data, list) else []

        return {
            "filename": file.filename,
            "path": file_path,
            "preview": preview,
            "total_records": len(data) if isinstance(data, list) else 0,
        }
    except HTTPException:
        # Re-raise HTTPExceptions to preserve status codes
        raise
    except Exception as e:
        logger.error(f"Error uploading dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datasets", response_model=DatasetListResponse)
async def list_datasets():
    """List all uploaded datasets."""
    return {"datasets": get_uploaded_datasets()}


@app.post("/api/quick-start-demo", response_model=QuickStartResponse)
async def quick_start_demo():
    """Load the facility support analyzer demo with dataset, prompt, and optimal configuration."""
    try:
        # Define paths to demo files
        demo_dataset_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "use-cases",
            "facility-support-analyzer",
            "dataset.json",
        )
        demo_prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "use-cases",
            "facility-support-analyzer",
            "facility_prompt_sys.txt",
        )

        # Check if demo files exist
        if not os.path.exists(demo_dataset_path):
            raise HTTPException(status_code=404, detail="Demo dataset file not found")
        if not os.path.exists(demo_prompt_path):
            raise HTTPException(status_code=404, detail="Demo prompt file not found")

        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Copy demo dataset to uploaded datasets directory
        demo_filename = "facility_support_demo.json"
        destination_path = os.path.join(UPLOAD_DIR, demo_filename)

        # Remove existing demo file if it exists
        if os.path.exists(destination_path):
            os.remove(destination_path)

        shutil.copy2(demo_dataset_path, destination_path)

        # Load and validate the dataset
        with open(destination_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise HTTPException(
                status_code=400, detail="Demo dataset must be a JSON array"
            )

        # Create preview (first 3 records)
        preview = data[:3] if len(data) > 3 else data

        # Load the demo prompt
        with open(demo_prompt_path, "r", encoding="utf-8") as f:
            demo_prompt = f.read().strip()

        # Define optimal configuration for facility support analyzer
        optimal_config = {
            "datasetAdapter": "facility",
            "metrics": "Facility Support",
            "model": "Llama 3.3 70B",
            "proposer": "Llama 3.3 70B",
            "strategy": "Basic",
            "useLlamaTips": True,
        }

        # Create dataset response
        dataset_response = DatasetUploadResponse(
            filename=demo_filename,
            path=destination_path,
            preview=preview,
            total_records=len(data),
        )

        logger.info(f"Quick start demo loaded successfully: {len(data)} records")

        return QuickStartResponse(
            success=True,
            dataset=dataset_response,
            prompt=demo_prompt,
            config=optimal_config,
            message=f"Demo loaded successfully! Facility Support Analyzer with {len(data)} sample records ready for optimization.",
        )

    except HTTPException:
        # Re-raise HTTPExceptions to preserve status codes
        raise
    except Exception as e:
        logger.error(f"Error loading quick start demo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load demo: {str(e)}")


@app.delete("/api/datasets/{filename}")
async def delete_dataset(filename: str):
    """Delete an uploaded dataset."""
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        os.remove(file_path)
        return {"message": f"Dataset {filename} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/datasets/analyze/{filename}", response_model=DatasetAnalysisResponse)
async def analyze_dataset(filename: str):
    """Analyze a dataset file and return field information with suggested mappings."""
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        analysis_result = dataset_analyzer.analyze_file(file_path)

        if "error" in analysis_result:
            return DatasetAnalysisResponse(
                total_records=0,
                sample_size=0,
                fields=[],
                suggestions={},
                sample_data=[],
                error=analysis_result["error"],
            )

        return DatasetAnalysisResponse(**analysis_result)

    except Exception as e:
        logger.error(f"Error analyzing dataset {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post(
    "/api/datasets/preview-transformation", response_model=PreviewTransformationResponse
)
async def preview_transformation(request: PreviewTransformationRequest):
    """Preview how dataset will be transformed with given field mappings."""
    file_path = os.path.join(UPLOAD_DIR, request.filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        preview_result = dataset_analyzer.preview_transformation(
            file_path, request.mappings, request.use_case
        )

        if "error" in preview_result:
            return PreviewTransformationResponse(
                original_data=[],
                transformed_data=[],
                adapter_config={},
                error=preview_result["error"],
            )

        return PreviewTransformationResponse(**preview_result)

    except Exception as e:
        logger.error(f"Error previewing transformation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@app.post("/api/datasets/save-mapping")
async def save_field_mapping(request: FieldMappingRequest):
    """Save field mapping configuration for a dataset."""
    file_path = os.path.join(UPLOAD_DIR, request.filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        # Generate adapter configuration
        adapter_config = dataset_analyzer.generate_adapter_config(
            request.mappings, request.use_case
        )

        # Save mapping configuration alongside the dataset
        mapping_file = os.path.join(UPLOAD_DIR, f"{request.filename}.mapping.json")
        with open(mapping_file, "w") as f:
            json.dump(
                {
                    "filename": request.filename,
                    "use_case": request.use_case,
                    "mappings": request.mappings,
                    "adapter_config": adapter_config,
                },
                f,
                indent=2,
            )

        return {
            "message": "Field mapping saved successfully",
            "adapter_config": adapter_config,
        }

    except Exception as e:
        logger.error(f"Error saving field mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save mapping: {str(e)}")


@app.post("/api/enhance-prompt", response_model=PromptResponse)
async def enhance_prompt(request: PromptRequest):
    """Enhance prompt using OpenRouter."""
    return await enhance_prompt_with_openrouter(
        request, ENHANCE_SYSTEM_MESSAGE, "enhance"
    )


@app.post("/api/migrate-prompt", response_model=PromptResponse)
async def migrate_prompt(request: PromptRequest):
    """Run llama-prompt-ops optimization based on frontend config."""
    # Check if llama-prompt-ops is available
    if not LLAMA_PROMPT_OPS_AVAILABLE:
        # Fall back to OpenRouter for prompt migration
        return await fallback_migrate_prompt(request)

    try:
        config = request.config or {}

        # API key precedence: env > client supplied
        api_key = os.getenv("OPENROUTER_API_KEY") or config.get("openrouterApiKey")
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="OpenRouter API key missing. Supply via UI or set OPENROUTER_API_KEY.",
            )

        # Set the API key in the environment so all components can access it
        # This is critical for metric evaluation which may create new model instances
        if api_key and not os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = api_key
            print("Set OPENROUTER_API_KEY from frontend configuration")

        # Get configuration from request or use defaults based on facility-simple.yaml
        task_model_name = MODEL_MAPPING.get(config.get("model", "llama-3.1-8b"))
        proposer_model_name = MODEL_MAPPING.get(config.get("proposer", "llama-3.1-8b"))
        optimization_level = STRATEGY_MAPPING.get(
            config.get("strategy", "Basic"), "basic"
        )
        use_llama_tips = config.get("useLlamaTips", True)

        # Get dataset adapter configuration
        dataset_adapter_name = config.get(
            "datasetAdapter", "facility"
        )  # Default to facility
        dataset_adapter_cfg = DATASET_ADAPTER_MAPPING.get(dataset_adapter_name)

        if not dataset_adapter_cfg:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset adapter '{dataset_adapter_name}' not found.",
            )

        # Get uploaded dataset info
        uploaded_datasets = get_uploaded_datasets()
        if not uploaded_datasets:
            raise HTTPException(
                status_code=400,
                detail="No dataset uploaded. Please upload a dataset first.",
            )

        # Use the first (and only) uploaded dataset
        dataset_info = uploaded_datasets[0]

        # Use selected metric from configuration - handle both old and new format
        metrics_config = config.get("metrics", "Exact Match")
        metric_configurations = config.get("metricConfigurations", {})

        # Handle new format (array of metrics) vs old format (single metric string)
        if isinstance(metrics_config, list) and len(metrics_config) > 0:
            # New format: use first metric for now (TODO: support multiple metrics)
            metric_name = metrics_config[0]
            metric_cfg = METRIC_MAPPING.get(metric_name)

            # Merge user configurations with default parameters
            if metric_cfg and metric_name in metric_configurations:
                user_config = metric_configurations[metric_name]
                # Update the metric parameters with user configurations
                metric_cfg = metric_cfg.copy()
                metric_cfg["params"] = {**metric_cfg["params"], **user_config}
        else:
            # Old format: single metric string
            metric_name = metrics_config
            metric_cfg = METRIC_MAPPING.get(metric_name)

        if not metric_cfg:
            # Fallback to Exact Match if metric not found
            metric_name = "exact_match"
            metric_cfg = {
                "class": "llama_prompt_ops.core.metrics.ExactMatchMetric",
                "params": {},
            }

            # Handle model configurations with new role naming
        model_configurations = config.get("modelConfigurations", [])
        target_model_config = None
        optimizer_model_config = None

        if model_configurations:
            # Separate models by role (using new naming: target/optimizer)
            for model_config in model_configurations:
                role = model_config.get("role", "both")
                if role in ["target", "both"]:
                    target_model_config = model_config
                if role in ["optimizer", "both"]:
                    optimizer_model_config = model_config

                # Set environment variables for API keys if provided
                if model_config.get("api_key"):
                    import os

                    provider_id = model_config["provider_id"]
                    if provider_id == "openrouter":
                        os.environ["OPENROUTER_API_KEY"] = model_config["api_key"]
                    elif provider_id == "together":
                        os.environ["TOGETHER_API_KEY"] = model_config["api_key"]
                    # Note: vLLM and NVIDIA NIM typically don't need API keys for local deployments

            # Use target model for task_model and optimizer model for proposer_model
            # This maintains compatibility with the existing YAML config format
            if target_model_config:
                target_model_name = f"{target_model_config['provider_id']}/{target_model_config['model_name']}"
            if optimizer_model_config:
                optimizer_model_name = f"{optimizer_model_config['provider_id']}/{optimizer_model_config['model_name']}"

        # Instantiate components --------------------------------------------------------
        try:
            # Print API key status for debugging (mask the actual key)
            if api_key:
                masked_key = (
                    api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
                    if len(api_key) > 8
                    else "****"
                )
                print(f"Using API key (masked): {masked_key}")
                print(
                    f"Environment API key set: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}"
                )

            task_model = setup_model(
                model_name=f"openrouter/{task_model_name}",
                api_key=api_key,
                temperature=0.0,
            )
            proposer_model = setup_model(
                model_name=f"openrouter/{proposer_model_name}",
                api_key=api_key,
                temperature=0.7,
            )

            metric_cls = load_class_dynamically(metric_cfg["class"])
            metric_params = metric_cfg.get("params", {})
            if issubclass(metric_cls, DSPyMetricAdapter):
                metric = metric_cls(model=task_model, **metric_params)
            else:
                metric = metric_cls(**metric_params)

            # Create dataset adapter using configuration-driven approach
            adapter_cls = load_class_dynamically(dataset_adapter_cfg["adapter_class"])

            # Get adapter parameters from configuration (not hardcoded)
            adapter_params = dataset_adapter_cfg.get("params", {}).copy()

            print(f"Using dataset adapter: {dataset_adapter_name}")
            print(f"Adapter parameters: {adapter_params}")

            # Create the adapter with the configured parameters
            adapter = adapter_cls(dataset_path=dataset_info["path"], **adapter_params)

            strategy = LlamaStrategy(
                model_name=task_model_name,
                metric=metric,
                auto=optimization_level,
                task_model=task_model,
                prompt_model=proposer_model,
            )

            migrator = PromptMigrator(
                strategy=strategy, task_model=task_model, prompt_model=proposer_model
            )

            # Dataset split (simple defaults)
            trainset, valset, testset = migrator.load_dataset_with_adapter(
                adapter, train_size=0.7, validation_size=0.15
            )

            # Query adapter for actual field names (don't assume)
            print("Querying adapter for field names...")
            # Get first example to inspect structure
            sample_data = adapter.adapt()[:1]

            if sample_data:
                input_fields = list(sample_data[0]["inputs"].keys())
                output_fields = list(sample_data[0]["outputs"].keys())
                print(f"Adapter produces input fields: {input_fields}")
                print(f"Adapter produces output fields: {output_fields}")
            else:
                # Fallback to defaults if no sample data
                input_fields = ["question"]
                output_fields = ["answer"]
                print("No sample data available, using default field names")

            # Prepare prompt data using the actual field names from the adapter
            prompt_data = {
                "text": request.prompt,
                "inputs": input_fields,  # Use what adapter actually produces
                "outputs": output_fields,  # Use what adapter actually produces
                # No field_mapping needed - adapter already handled the mapping
            }

            print(f"Prompt data configuration: {prompt_data}")

            # Execute optimization ----------------------------------------------------------
            optimized_program = migrator.optimize(
                prompt_data,
                trainset=trainset,
                valset=valset,
                testset=testset,
                use_llama_tips=use_llama_tips,
            )

            # Extract the optimized prompt from the program
            optimized_prompt = optimized_program.signature.instructions
            print(
                f"Optimized prompt extracted: {optimized_prompt[:100]}..."
            )  # Show first 100 chars

            return {"optimizedPrompt": optimized_prompt}

        except Exception as component_error:
            # Log the detailed error for debugging
            print(f"Error during llama-prompt-ops component setup: {component_error}")
            traceback.print_exc()

            # Fall back to OpenRouter
            print("Falling back to OpenRouter for prompt migration")
            return await fallback_migrate_prompt(request)

    except Exception as exc:
        print(f"Unexpected error in migrate_prompt: {exc}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error migrating prompt: {str(exc)}"
        )


async def fallback_migrate_prompt(request: PromptRequest):
    """Fallback to OpenRouter for prompt migration when llama-prompt-ops is unavailable."""
    return await enhance_prompt_with_openrouter(
        request, ENHANCE_SYSTEM_MESSAGE, "fallback_migrate"
    )


@app.post("/generate-config")
async def generate_config(request: dict):
    """
    Generate YAML configuration from onboarding wizard data.
    Optionally save to disk if save_to_disk is True.
    """
    try:
        wizard_data = request.get("wizardData", {})
        project_name = request.get("projectName", "generated-project")
        save_to_disk = request.get("saveToYaml", False)

        transformer = ConfigurationTransformer()
        config_dict = transformer.transform(wizard_data, project_name)
        config_yaml = transformer.generate_yaml_string(wizard_data, project_name)

        response = {"success": True, "config": config_dict, "yaml": config_yaml}

        # Optionally save YAML file to disk
        if save_to_disk:
            uploads_dir = os.path.join(os.path.dirname(__file__), "uploaded_datasets")
            os.makedirs(uploads_dir, exist_ok=True)

            yaml_filename = f"{project_name}-config.yaml"
            yaml_path = os.path.join(uploads_dir, yaml_filename)

            with open(yaml_path, "w") as f:
                f.write(config_yaml)

            response["saved_path"] = yaml_path
            response["filename"] = yaml_filename
            response["message"] = f"Configuration saved as {yaml_filename}"

        return response
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/create-project")
async def create_project(request: dict):
    """
    Create a complete project structure with config, prompt, and dataset files.
    """
    try:
        wizard_data = request.get("wizardData", {})
        requested_project_name = request.get("projectName", "generated-project")

        # Create project in uploads directory
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploaded_datasets")

        # Generate unique project name to avoid conflicts
        unique_project_name = generate_unique_project_name(
            requested_project_name, uploads_dir
        )
        logger.info(f"Requested project name: {requested_project_name}")
        logger.info(f"Using unique project name: {unique_project_name}")

        # Fix dataset path to point to actual uploaded file
        dataset_info = wizard_data.get("dataset", {})
        if "path" in dataset_info:
            # Convert relative filename to absolute path in uploads directory
            dataset_filename = dataset_info["path"]
            dataset_absolute_path = os.path.join(uploads_dir, dataset_filename)
            wizard_data["dataset"]["path"] = dataset_absolute_path

        transformer = ConfigurationTransformer()
        created_files = transformer.create_project_structure(
            wizard_data, uploads_dir, unique_project_name
        )

        return {
            "success": True,
            "projectPath": os.path.join(uploads_dir, unique_project_name),
            "createdFiles": created_files,
            "message": f"Project '{unique_project_name}' created successfully",
            "actualProjectName": unique_project_name,  # Include actual name used
            "requestedProjectName": requested_project_name,  # Include requested name for comparison
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/download-config/{project_name}")
async def download_config(project_name: str):
    """
    Download the config.yaml file for a generated project.
    """
    try:
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploaded_datasets")
        config_path = os.path.join(uploads_dir, project_name, "config.yaml")

        if not os.path.exists(config_path):
            raise HTTPException(status_code=404, detail="Config file not found")

        return FileResponse(
            config_path,
            media_type="application/x-yaml",
            filename=f"{project_name}-config.yaml",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@app.websocket("/ws/optimize/{project_name}")
async def optimize_with_streaming(websocket: WebSocket, project_name: str):
    """
    WebSocket endpoint for real-time optimization with streaming logs.
    """
    await websocket.accept()

    # Initialize optimization manager
    manager = OptimizationManager(websocket)

    try:
        await manager.send_status("Initializing optimization...", "setup")

        # Set up log streaming to capture all output
        manager.setup_log_streaming()

        # Find the project directory
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploaded_datasets")
        project_path = os.path.join(uploads_dir, project_name)

        if not os.path.exists(project_path):
            await manager.send_error(f"Project '{project_name}' not found")
            return

        config_path = os.path.join(project_path, "config.yaml")
        if not os.path.exists(config_path):
            await manager.send_error(
                f"Config file not found in project '{project_name}'"
            )
            return

        await manager.send_status("Loading configuration...", "config")

        # Load configuration (reuse logic from migrate-prompt endpoint)
        try:
            with open(config_path, "r") as f:
                config_dict = yaml.safe_load(f)
        except Exception as e:
            await manager.send_error(f"Failed to load config: {str(e)}")
            return

        await manager.send_status("Setting up models and dataset...", "setup")

        # Check if llama-prompt-ops is available
        if not LLAMA_PROMPT_OPS_AVAILABLE:
            await manager.send_error(
                "llama-prompt-ops is not available. Please install it."
            )
            return

        # Get API key from config or environment
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            await manager.send_error(
                "API key not found. Please set OPENROUTER_API_KEY environment variable."
            )
            return

        # Set API key in environment for all components
        os.environ["OPENROUTER_API_KEY"] = api_key

        # Extract configuration (copy logic from migrate-prompt endpoint)
        model_config = config_dict.get("model", {})
        dataset_config = config_dict.get("dataset", {})
        metric_config = config_dict.get("metric", {})
        optimization_config = config_dict.get("optimization", {})

        # Setup models
        task_model_name = model_config.get(
            "task_model", "openrouter/meta-llama/llama-3.3-70b-instruct"
        )
        proposer_model_name = model_config.get("proposer_model", task_model_name)

        await manager.send_progress(
            "models", 25, f"Setting up task model: {task_model_name}"
        )

        task_model = setup_model(
            model_name=task_model_name,
            api_key=api_key,
            temperature=model_config.get("temperature", 0.0),
        )

        await manager.send_progress(
            "models", 50, f"Setting up proposer model: {proposer_model_name}"
        )

        proposer_model = setup_model(
            model_name=proposer_model_name,
            api_key=api_key,
            temperature=0.7,
        )

        # Setup metric
        await manager.send_progress("metric", 75, "Setting up evaluation metric...")

        metric_class_path = metric_config.get(
            "class", "llama_prompt_ops.core.metrics.ExactMatchMetric"
        )
        metric_cls = load_class_dynamically(metric_class_path)
        metric_params = {k: v for k, v in metric_config.items() if k != "class"}

        if issubclass(metric_cls, DSPyMetricAdapter):
            metric = metric_cls(model=task_model, **metric_params)
        else:
            metric = metric_cls(**metric_params)

        # Setup dataset adapter
        await manager.send_progress("dataset", 85, "Loading dataset...")

        adapter_class_path = dataset_config.get(
            "adapter_class", "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter"
        )
        adapter_cls = load_class_dynamically(adapter_class_path)

        dataset_path = os.path.join(project_path, "data", "dataset.json")
        adapter_params = {
            k: v
            for k, v in dataset_config.items()
            if k not in ["adapter_class", "path"]
        }
        adapter = adapter_cls(dataset_path=dataset_path, **adapter_params)

        # Setup strategy and migrator
        await manager.send_progress(
            "setup", 95, "Initializing optimization strategy..."
        )

        from llama_prompt_ops.core.model_strategies import LlamaStrategy

        strategy = LlamaStrategy(
            model_name=task_model_name,
            metric=metric,
            auto=optimization_config.get("strategy", "basic"),
            task_model=task_model,
            prompt_model=proposer_model,
        )

        migrator = PromptMigrator(
            strategy=strategy, task_model=task_model, prompt_model=proposer_model
        )

        # Load dataset splits
        trainset, valset, testset = migrator.load_dataset_with_adapter(
            adapter,
            train_size=dataset_config.get("train_size", 0.5),
            validation_size=dataset_config.get("validation_size", 0.2),
        )

        # Load prompt
        prompt_config = config_dict.get("system_prompt", {})
        prompt_file = prompt_config.get("file")
        prompt_text = prompt_config.get("text", "")

        if prompt_file and not prompt_text:
            prompt_file_path = os.path.join(project_path, prompt_file)
            if os.path.exists(prompt_file_path):
                with open(prompt_file_path, "r") as f:
                    prompt_text = f.read()

        prompt_data = {
            "text": prompt_text,
            "inputs": prompt_config.get("inputs", ["question"]),
            "outputs": prompt_config.get("outputs", ["answer"]),
        }

        await manager.send_status("Starting optimization...", "optimize")
        await manager.send_progress(
            "optimize", 0, "Beginning prompt optimization process..."
        )

        # Run optimization - this will stream all logs automatically
        optimized_program = migrator.optimize(
            prompt_data,
            trainset=trainset,
            valset=valset,
            testset=testset,
            use_llama_tips=optimization_config.get("use_llama_tips", True),
        )

        # Extract results
        optimized_prompt = optimized_program.signature.instructions

        await manager.send_result(
            {
                "success": True,
                "optimizedPrompt": optimized_prompt,
                "originalPrompt": prompt_text,
                "projectName": project_name,
                "projectPath": project_path,
                "message": "Optimization completed successfully!",
            }
        )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected during optimization of {project_name}")
    except Exception as e:
        logger.error(f"Error during optimization: {str(e)}")
        try:
            await manager.send_error(f"Optimization failed: {str(e)}")
        except:
            # WebSocket might be closed
            pass
    finally:
        # Always clean up log handlers
        manager.cleanup_log_streaming()


# --- Main ----------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
