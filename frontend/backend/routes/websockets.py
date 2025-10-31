"""
WebSocket endpoints for real-time optimization streaming.
"""

import logging
import os

import yaml
from config import UPLOAD_DIR
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from utils import OptimizationManager, load_class_dynamically

logger = logging.getLogger(__name__)
router = APIRouter()

# Check for llama-prompt-ops availability
try:
    from llama_prompt_ops.core.metrics import DSPyMetricAdapter
    from llama_prompt_ops.core.migrator import PromptMigrator
    from llama_prompt_ops.core.model import setup_model
    from llama_prompt_ops.core.model_strategies import LlamaStrategy

    LLAMA_PROMPT_OPS_AVAILABLE = True
except ImportError:
    LLAMA_PROMPT_OPS_AVAILABLE = False


@router.websocket("/ws/optimize/{project_name}")
async def optimize_with_streaming(websocket: WebSocket, project_name: str):
    """WebSocket endpoint for real-time optimization with streaming logs."""
    await websocket.accept()

    # Initialize optimization manager
    manager = OptimizationManager(websocket)

    try:
        await manager.send_status("Initializing optimization...", "setup")

        # Set up log streaming to capture all output
        manager.setup_log_streaming()

        # Find the project directory
        uploads_dir = UPLOAD_DIR
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

        # Load configuration
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

        # Extract configuration
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
