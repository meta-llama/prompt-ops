"""
Prompt enhancement and migration endpoints.
"""

import logging
import os
import traceback
from typing import Any, Dict, Optional

from config import (
    DATASET_ADAPTER_MAPPING,
    ENHANCE_SYSTEM_PROMPT,
    FAIL_ON_ERROR,
    METRIC_MAPPING,
    MODEL_MAPPING,
    STRATEGY_MAPPING,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils import (
    create_llm_completion,
    get_uploaded_datasets,
    load_class_dynamically,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Check for llama-prompt-ops availability (copy from main.py)
try:
    from llama_prompt_ops.core.datasets import ConfigurableJSONAdapter
    from llama_prompt_ops.core.metrics import DSPyMetricAdapter
    from llama_prompt_ops.core.migrator import PromptMigrator
    from llama_prompt_ops.core.model import setup_model
    from llama_prompt_ops.core.model_strategies import LlamaStrategy

    LLAMA_PROMPT_OPS_AVAILABLE = True
except ImportError:
    LLAMA_PROMPT_OPS_AVAILABLE = False


# Pydantic models
class PromptRequest(BaseModel):
    prompt: str
    config: Optional[Dict[str, Any]] = None


class PromptResponse(BaseModel):
    optimizedPrompt: str


async def enhance_prompt_with_openrouter(
    request: PromptRequest, system_message: str, operation_name: str = "processing"
):
    """
    Enhance prompts using LiteLLM (supports any provider via model prefix).
    LiteLLM reads API keys from environment unless explicitly provided.
    """
    config = request.config or {}

    # Get API configuration from request
    api_key = config.get("apiKey") or config.get("openrouterApiKey")
    api_base = config.get("apiBaseUrl")
    model = config.get("model")

    # Handle legacy MODEL_MAPPING if friendly name provided
    if model in MODEL_MAPPING:
        model = MODEL_MAPPING[model]

    # If user provides an API key, we'll pass it to litellm
    # Otherwise, litellm will read from environment automatically based on model prefix

    try:
        print(
            f"🎯 Enhance endpoint - Model: {model}, API Base: {api_base or 'default'}"
        )

        # Use LiteLLM for completion
        response = create_llm_completion(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": request.prompt},
            ],
            api_key=api_key,
            api_base=api_base,
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


async def enhance_prompt_with_litellm(
    request: PromptRequest, system_message: str, operation_name: str = "processing"
):
    """
    Enhance prompts using LiteLLM with automatic provider detection.

    LiteLLM will automatically detect the provider from the model name and
    fetch the appropriate API key from environment variables:
    - openrouter/* -> OPENROUTER_API_KEY
    - openai/* -> OPENAI_API_KEY
    - anthropic/* -> ANTHROPIC_API_KEY
    - together_ai/* -> TOGETHER_API_KEY
    - meta-llama/* -> LLAMA_API_KEY
    - etc.
    """
    from litellm import completion

    config = request.config or {}

    # Get model from config
    model = config.get("model")
    api_base = config.get("apiBaseUrl")  # Optional custom base URL

    # Handle legacy MODEL_MAPPING if friendly name provided
    if model in MODEL_MAPPING:
        model = MODEL_MAPPING[model]

    if not model:
        raise HTTPException(
            status_code=400,
            detail="Model not specified in request config.",
        )

    try:
        print(
            f"🎯 LiteLLM Enhance - Model: {model}, API Base: {api_base or 'auto-detected'}"
        )

        # Build completion kwargs - let LiteLLM handle API key from env
        completion_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": request.prompt},
            ],
            "temperature": 0.7,
        }

        # Only add api_base if explicitly provided
        if api_base:
            completion_kwargs["api_base"] = api_base

        # Log the full request payload
        print(f"📤 LiteLLM Request Payload: {completion_kwargs}")

        # LiteLLM auto-detects provider from model name and fetches API key from env
        response = completion(**completion_kwargs)

        enhanced_prompt = response.choices[0].message.content.strip()
        return {"optimizedPrompt": enhanced_prompt}

    except Exception as e:
        print(f"Error in {operation_name}: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error {operation_name} prompt: {str(e)}"
        )


@router.post("/api/enhance-prompt", response_model=PromptResponse)
async def enhance_prompt(request: PromptRequest):
    """Enhance prompt using LiteLLM with automatic provider detection."""
    return await enhance_prompt_with_litellm(request, ENHANCE_SYSTEM_PROMPT, "enhance")


@router.post("/api/migrate-prompt", response_model=PromptResponse)
async def migrate_prompt(request: PromptRequest):
    """Run llama-prompt-ops optimization based on frontend config."""
    config = request.config or {}

    # Get fail_on_error setting - if True, raise errors instead of falling back
    # Priority: request config > global env var (FAIL_ON_ERROR)
    fail_on_error = config.get("failOnError", FAIL_ON_ERROR)

    # Check if llama-prompt-ops is available
    if not LLAMA_PROMPT_OPS_AVAILABLE:
        if fail_on_error:
            raise HTTPException(
                status_code=500,
                detail="llama-prompt-ops is not available. Cannot proceed with strict mode enabled.",
            )
        # Fall back to OpenRouter for prompt migration
        return await enhance_prompt_with_openrouter(
            request, ENHANCE_SYSTEM_PROMPT, "fallback_migrate"
        )

    try:

        # API key precedence: env > client supplied
        api_key = os.getenv("OPENROUTER_API_KEY") or config.get("openrouterApiKey")
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="OpenRouter API key missing. Supply via UI or set OPENROUTER_API_KEY.",
            )

        # Set the API key in the environment so all components can access it
        if api_key and not os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = api_key
            print("Set OPENROUTER_API_KEY from frontend configuration")

        # Get configuration from request or use defaults
        task_model_name = MODEL_MAPPING.get(
            config.get("model", "Llama 3.1 8B"), "meta-llama/llama-3.1-8b-instruct"
        )
        proposer_model_name = MODEL_MAPPING.get(
            config.get("proposer", "Llama 3.1 8B"), "meta-llama/llama-3.1-8b-instruct"
        )
        optimization_level = STRATEGY_MAPPING.get(
            config.get("strategy", "Basic"), "basic"
        )
        use_llama_tips = config.get("useLlamaTips", True)

        # Get dataset adapter configuration
        dataset_adapter_name = config.get("datasetAdapter", "facility")
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
        metrics_config = config.get("metrics", "Exact Match")
        metric_configurations = config.get("metricConfigurations", {})

        # Handle new format (array of metrics) vs old format (single metric string)
        if isinstance(metrics_config, list) and len(metrics_config) > 0:
            metric_name = metrics_config[0]
            metric_cfg = METRIC_MAPPING.get(metric_name)
            if metric_cfg and metric_name in metric_configurations:
                user_config = metric_configurations[metric_name]
                metric_cfg = metric_cfg.copy()
                metric_cfg["params"] = {**metric_cfg["params"], **user_config}
        else:
            metric_name = metrics_config
            metric_cfg = METRIC_MAPPING.get(metric_name)
            # Apply user customizations for backward-compatible string format too
            if metric_cfg and metric_name in metric_configurations:
                user_config = metric_configurations[metric_name]
                metric_cfg = metric_cfg.copy()
                metric_cfg["params"] = {**metric_cfg["params"], **user_config}

        if not metric_cfg:
            metric_name = "exact_match"
            metric_cfg = {
                "class": "llama_prompt_ops.core.metrics.ExactMatchMetric",
                "params": {},
            }

        # Handle model configurations
        model_configurations = config.get("modelConfigurations", [])
        target_model_config = None
        optimizer_model_config = None

        # Variables to store final model names
        final_task_model_name = task_model_name
        final_proposer_model_name = proposer_model_name

        if model_configurations:
            for model_config in model_configurations:
                role = model_config.get("role", "both")
                if role in ["target", "both"]:
                    target_model_config = model_config
                if role in ["optimizer", "both"]:
                    optimizer_model_config = model_config

                if model_config.get("api_key"):
                    provider_id = model_config.get("provider_id")
                    if provider_id == "openrouter":
                        os.environ["OPENROUTER_API_KEY"] = model_config["api_key"]
                    elif provider_id == "together":
                        os.environ["TOGETHER_API_KEY"] = model_config["api_key"]

            # Use custom model configs if provided
            if target_model_config:
                provider_id = target_model_config.get("provider_id")
                model_name = target_model_config.get("model_name")
                if provider_id and model_name:
                    final_task_model_name = f"{provider_id}/{model_name}"
            if optimizer_model_config:
                provider_id = optimizer_model_config.get("provider_id")
                model_name = optimizer_model_config.get("model_name")
                if provider_id and model_name:
                    final_proposer_model_name = f"{provider_id}/{model_name}"

        # Instantiate components
        try:
            # Model names should include provider prefix (e.g., openrouter/meta-llama/...)
            task_model_full = final_task_model_name
            proposer_model_full = final_proposer_model_name

            task_model = setup_model(
                model_name=task_model_full,
                api_key=api_key,
                temperature=0.0,
            )
            proposer_model = setup_model(
                model_name=proposer_model_full,
                api_key=api_key,
                temperature=0.7,
            )

            metric_cls = load_class_dynamically(metric_cfg["class"])
            metric_params = metric_cfg.get("params", {})
            if issubclass(metric_cls, DSPyMetricAdapter):
                metric = metric_cls(model=task_model, **metric_params)
            else:
                metric = metric_cls(**metric_params)

            # Create dataset adapter
            adapter_cls = load_class_dynamically(dataset_adapter_cfg["adapter_class"])
            adapter_params = dataset_adapter_cfg.get("params", {}).copy()
            adapter = adapter_cls(dataset_path=dataset_info["path"], **adapter_params)

            strategy = LlamaStrategy(
                model_name=task_model_name,
                metric=metric,
                auto=optimization_level,
                task_model=task_model,
                prompt_model=proposer_model,
                fail_on_error=fail_on_error,
            )

            migrator = PromptMigrator(
                strategy=strategy, task_model=task_model, prompt_model=proposer_model
            )

            # Dataset split
            trainset, valset, testset = migrator.load_dataset_with_adapter(
                adapter, train_size=0.7, validation_size=0.15
            )

            # Query adapter for actual field names
            sample_data = adapter.adapt()[:1]
            if sample_data:
                input_fields = list(sample_data[0]["inputs"].keys())
                output_fields = list(sample_data[0]["outputs"].keys())
            else:
                input_fields = ["question"]
                output_fields = ["answer"]

            # Prepare prompt data
            prompt_data = {
                "text": request.prompt,
                "inputs": input_fields,
                "outputs": output_fields,
            }

            # Execute optimization
            optimized_program = migrator.optimize(
                prompt_data,
                trainset=trainset,
                valset=valset,
                testset=testset,
                use_llama_tips=use_llama_tips,
            )

            # Extract the optimized prompt
            optimized_prompt = optimized_program.signature.instructions
            return {"optimizedPrompt": optimized_prompt}

        except Exception as component_error:
            print(f"Error during llama-prompt-ops component setup: {component_error}")
            traceback.print_exc()
            if fail_on_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Optimization failed: {str(component_error)}",
                )
            print("Falling back to OpenRouter for prompt migration")
            return await enhance_prompt_with_openrouter(
                request, ENHANCE_SYSTEM_PROMPT, "fallback_migrate"
            )

    except Exception as exc:
        print(f"Unexpected error in migrate_prompt: {exc}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error migrating prompt: {str(exc)}"
        )
