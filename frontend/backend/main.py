import importlib
import importlib.util
import os
import subprocess
import sys
import traceback
from typing import Any, Dict, Optional

import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    print("The /api/migrate-prompt endpoint will fall back to OpenAI")
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
app = FastAPI(title="Prompt Love Alchemy API")

# CORS for local development; tighten in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize OpenAI client – only used for enhance endpoint
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print(
        "Warning: OPENAI_API_KEY not found in environment variables. /enhance endpoint will fail."
    )
client = openai.OpenAI(api_key=openai_api_key)

# --- Configuration Mappings ---
MODEL_MAPPING = {
    "Llama 3.3 70B": "meta-llama/llama-3.1-70b-instruct",
    "Llama 3.1 8B": "meta-llama/llama-3.1-8b-instruct",
    "Llama 2 13B": "meta-llama/llama-2-13b-chat",
    "GPT-4": "openai/gpt-4",
}

METRIC_MAPPING = {
    "Similarity": {
        "class": "llama_prompt_ops.core.metrics.DSPyMetricAdapter",
        "params": {"signature_name": "similarity"},
    }
}

DATASET_MAPPING = {
    "Q&A": {
        "adapter_class": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
        "path": os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "llama-prompt-ops",
                "use-cases",
                "facility-support-analyzer",
                "dataset.json",
            )
        ),
        "params": {
            "input_field": ["fields", "input"],
            "golden_output_field": "answer",
        },
    }
}

STRATEGY_MAPPING = {"MiPro": "basic", "GEPA": "advanced", "Infer": "intermediate"}

# --- Utility -------------------------------------------------------------


def load_class_dynamically(class_path: str):
    """Import and return class from dotted path string."""
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


# --- Pydantic Models -----------------------------------------------------


class PromptRequest(BaseModel):
    prompt: str
    config: Optional[Dict[str, Any]] = None


class PromptResponse(BaseModel):
    optimizedPrompt: str


# --- Routes --------------------------------------------------------------


@app.options("/api/enhance-prompt")
@app.options("/api/migrate-prompt")
async def options_route():
    return {"status": "OK"}


@app.post("/api/enhance-prompt", response_model=PromptResponse)
async def enhance_prompt(request: PromptRequest):
    if not openai_api_key:
        raise HTTPException(
            status_code=500, detail="OPENAI_API_KEY not configured on server."
        )
    system_message = (
        "You are an expert prompt engineer. Improve the given prompt for clarity, "
        "specificity and effectiveness. Return ONLY the enhanced prompt."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": request.prompt},
            ],
            temperature=0.7,
        )
        return {"optimizedPrompt": response.choices[0].message.content.strip()}
    except Exception as exc:
        print(f"/enhance failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/migrate-prompt", response_model=PromptResponse)
async def migrate_prompt(request: PromptRequest):
    """Run llama-prompt-ops optimization based on frontend config."""
    # Check if llama-prompt-ops is available
    if not LLAMA_PROMPT_OPS_AVAILABLE:
        # Fall back to OpenAI for prompt migration
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

        # Get configuration from request or use defaults based on facility-simple.yaml
        task_model_name = MODEL_MAPPING.get(config.get("model", "Llama 3.3 70B"))
        proposer_model_name = MODEL_MAPPING.get(config.get("proposer", "Llama 3.3 70B"))
        optimization_level = STRATEGY_MAPPING.get(
            config.get("strategy", "MiPro"), "basic"
        )
        use_llama_tips = config.get("useLlamaTips", True)
        dataset_cfg = DATASET_MAPPING.get(config.get("dataset", "Q&A"))

        # Use FacilityMetric as default from facility-simple.yaml
        metric_cfg = {
            "class": "llama_prompt_ops.core.metrics.FacilityMetric",
            "params": {"strict_json": False, "output_field": "answer"},
        }

        # Instantiate components --------------------------------------------------------
        try:
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

            adapter_cls = load_class_dynamically(dataset_cfg["adapter_class"])
            adapter = adapter_cls(
                dataset_path=dataset_cfg["path"], **dataset_cfg.get("params", {})
            )

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

            # Create a custom field adapter to handle the nested 'fields' structure
            # This avoids the conflict with DSPy's signature system
            class CustomFieldAdapter:
                def __init__(self, data):
                    self.data = data

                def get_input(self, item):
                    # Extract nested input from fields.input
                    if "fields" in item and "input" in item["fields"]:
                        return item["fields"]["input"]
                    return None

                def get_output(self, item):
                    # Extract answer directly
                    return item.get("answer")

            # Create a field mapping to handle the nested structure
            field_mapping = {
                "question": lambda x: (
                    x["fields"]["input"]
                    if "fields" in x and "input" in x["fields"]
                    else None
                )
            }

            # Prepare prompt data with the custom field mapping
            prompt_data = {
                "text": request.prompt,
                "inputs": ["question"],  # Use a simple field name to avoid conflicts
                "outputs": ["answer"],
                "field_mapping": field_mapping,  # Add the custom mapping
            }

            # Execute optimization ----------------------------------------------------------
            optimized_program = migrator.optimize(
                prompt_data,
                trainset=trainset,
                valset=valset,
                testset=testset,
                use_llama_tips=use_llama_tips,
            )
            optimized_prompt = optimized_program.signature.instructions
            return {"optimizedPrompt": optimized_prompt}

        except Exception as component_error:
            # Log the detailed error for debugging
            print(f"Error during llama-prompt-ops component setup: {component_error}")
            traceback.print_exc()

            # Fall back to OpenAI
            print("Falling back to OpenAI for prompt migration")
            return await fallback_migrate_prompt(request)

    except Exception as exc:
        print(f"Unexpected error in migrate_prompt: {exc}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error migrating prompt: {str(exc)}"
        )


async def fallback_migrate_prompt(request: PromptRequest):
    """Fallback to OpenAI for prompt migration when llama-prompt-ops is unavailable."""
    if not openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY not configured on server and llama-prompt-ops is unavailable.",
        )

    try:
        # Use OpenAI to migrate the prompt
        system_message = """You are an expert prompt engineer specializing in Llama models.
        Your task is to migrate the given prompt to work effectively with Llama models.

        Apply these Llama-specific best practices:
        - Use clear and concise instructions
        - Place important instructions at the beginning or end of the prompt
        - Specify the desired format for the output
        - Break down complex tasks into steps
        - For Llama 3, use XML-style tags to structure different parts of the prompt
        - Avoid overly complex nested structures
        - Be explicit about what the model should not do
        - Provide examples for complex tasks

        Maintain the original intent but adapt the format, style, and structure to work optimally with Llama.
        Return only the migrated prompt with no explanations."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": request.prompt},
            ],
            temperature=0.7,
        )

        migrated_prompt = response.choices[0].message.content.strip()
        return {"optimizedPrompt": migrated_prompt}
    except Exception as e:
        print(f"Error in fallback migration: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error migrating prompt: {str(e)}")


# --- Main ----------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
