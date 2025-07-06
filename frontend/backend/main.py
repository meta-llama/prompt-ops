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
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("backend.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

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
    os.path.join(os.path.dirname(__file__), "..", "llama-prompt-ops", "src")
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
            "input_field": ["fields", "input"],  # Nested path for facility dataset
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
    dataset_adapters: Dict[str, Dict]  # Changed from datasets to dataset_adapters
    strategies: Dict[str, str]


class DatasetUploadResponse(BaseModel):
    filename: str
    path: str
    preview: List[Dict[str, Any]]
    total_records: int


class DatasetListResponse(BaseModel):
    datasets: List[Dict[str, Any]]


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


# --- Routes --------------------------------------------------------------


@app.options("/api/enhance-prompt")
@app.options("/api/migrate-prompt")
@app.options("/api/configurations")
@app.options("/api/datasets/upload")
@app.options("/api/datasets")
@app.options("/api/datasets/{filename}")
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

        # Use selected metric from configuration
        metric_name = config.get("metrics", "Exact Match")
        metric_cfg = METRIC_MAPPING.get(metric_name)

        if not metric_cfg:
            # Fallback to Exact Match if metric not found
            metric_cfg = {
                "class": "llama_prompt_ops.core.metrics.ExactMatchMetric",
                "params": {},
            }

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
            sample_data = adapter.adapt()[:1]  # Get first example to inspect structure

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


# --- Main ----------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
