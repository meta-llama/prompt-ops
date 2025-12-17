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
    get_uploaded_datasets,
    load_class_dynamically,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Import shared core module with availability checks
from core import (
    LLAMA_PROMPT_OPS_AVAILABLE,
    BasicOptimizationStrategy,
    ConfigurableJSONAdapter,
    DSPyMetricAdapter,
    PromptMigrator,
    setup_model,
)


# Pydantic models
class PromptRequest(BaseModel):
    prompt: str
    config: Optional[Dict[str, Any]] = None


class PromptResponse(BaseModel):
    optimizedPrompt: str


@router.post("/api/enhance-prompt", response_model=PromptResponse)
async def enhance_prompt(request: PromptRequest):
    """
    Enhance prompt using LiteLLM with automatic provider detection.

    LiteLLM detects the provider from the model name and fetches API key from env:
    - openrouter/* -> OPENROUTER_API_KEY
    - openai/* -> OPENAI_API_KEY
    - anthropic/* -> ANTHROPIC_API_KEY
    - together_ai/* -> TOGETHER_API_KEY
    """
    from litellm import completion

    config = request.config or {}
    model = config.get("model")
    api_base = config.get("apiBaseUrl")

    # Handle legacy MODEL_MAPPING if friendly name provided
    if model in MODEL_MAPPING:
        model = MODEL_MAPPING[model]

    if not model:
        raise HTTPException(
            status_code=400, detail="Model not specified in request config."
        )

    try:
        import time

        start_time = time.monotonic()
        logger.info(
            f"Enhance - Model: {model}, API Base: {api_base or 'auto-detected'}"
        )

        completion_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": ENHANCE_SYSTEM_PROMPT},
                {"role": "user", "content": request.prompt},
            ],
            "temperature": 0.7,
        }
        if api_base:
            completion_kwargs["api_base"] = api_base

        response = completion(**completion_kwargs)
        logger.info(
            f"Enhance response received in {time.monotonic() - start_time:.2f} seconds"
        )
        enhanced_prompt = response.choices[0].message.content.strip()
        return {"optimizedPrompt": enhanced_prompt}

    except Exception as e:
        logger.error(f"Error enhancing prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Error enhancing prompt: {str(e)}")


@router.post("/api/migrate-prompt", response_model=PromptResponse)
async def migrate_prompt(request: PromptRequest):
    """Run prompt-ops optimization based on frontend config."""
    config = request.config or {}

    # Get fail_on_error setting - if True, raise errors instead of falling back
    # Priority: request config > global env var (FAIL_ON_ERROR)
    fail_on_error = config.get("failOnError", FAIL_ON_ERROR)

    # Check if prompt-ops is available
    if not LLAMA_PROMPT_OPS_AVAILABLE:
        if fail_on_error:
            raise HTTPException(
                status_code=500,
                detail="prompt-ops is not available. Cannot proceed with strict mode enabled.",
            )
        else:
            # Fall back to simple enhancement
            return await enhance_prompt(request)

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
            logger.info("Set OPENROUTER_API_KEY from frontend configuration")

        # Get configuration from request or use defaults
        task_model_name = MODEL_MAPPING.get(
            config.get("model", "Llama 3.1 8B"),
            "openrouter/meta-llama/llama-3.1-8b-instruct",
        )
        proposer_model_name = MODEL_MAPPING.get(
            config.get("proposer", "Llama 3.1 8B"),
            "openrouter/meta-llama/llama-3.1-8b-instruct",
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
                "class": "prompt_ops.core.metrics.ExactMatchMetric",
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

            strategy = BasicOptimizationStrategy(
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
            logger.error(f"Error during prompt-ops component setup: {component_error}")
            traceback.print_exc()
            if fail_on_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Optimization failed: {str(component_error)}",
                )
            else:
                logger.info("Falling back to simple enhancement")
                return await enhance_prompt(request)

    except Exception as exc:
        logger.error(f"Unexpected error in migrate_prompt: {exc}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error migrating prompt: {str(exc)}"
        )
