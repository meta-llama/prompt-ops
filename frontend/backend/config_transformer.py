"""
Configuration transformer service for converting onboarding wizard data
to llama-prompt-ops YAML configuration format.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Union

import yaml


class ConfigurationTransformer:
    """
    Transforms onboarding wizard data into llama-prompt-ops compatible YAML configuration.
    """

    # Mapping from frontend metric IDs to backend metric classes
    METRIC_ID_MAPPING = {
        "exact_match": {
            "class": "llama_prompt_ops.core.metrics.ExactMatchMetric",
            "default_params": {},
        },
        "semantic_similarity": {
            "class": "llama_prompt_ops.core.metrics.DSPyMetricAdapter",
            "default_params": {"signature_name": "similarity"},
        },
        "correctness": {
            "class": "llama_prompt_ops.core.metrics.DSPyMetricAdapter",
            "default_params": {"signature_name": "correctness"},
        },
        "json_structured": {
            "class": "llama_prompt_ops.core.metrics.StandardJSONMetric",
            "default_params": {},
        },
        "facility_metric": {
            "class": "llama_prompt_ops.core.metrics.FacilityMetric",
            "default_params": {"strict_json": False},
        },
    }

    # Fallback mapping for legacy use case-based configuration
    USE_CASE_FALLBACK_METRICS = {
        "qa": "exact_match",
        "rag": "semantic_similarity",
        "classification": "exact_match",
        "summarization": "semantic_similarity",
        "extraction": "json_structured",
        "custom": "exact_match",
    }

    # Mapping from wizard dataset types to adapter configurations
    DATASET_FIELD_MAPPING = {
        "qa": {
            "adapter_class": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
            "input_field": "question",
            "golden_output_field": "answer",
        },
        "rag": {
            "adapter_class": "llama_prompt_ops.core.datasets.RAGJSONAdapter",
            "question_field": "query",
            "context_field": "context",
            "golden_answer_field": "answer",
        },
        "classification": {
            "adapter_class": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
            "input_field": "text",
            "golden_output_field": "category",
        },
        "summarization": {
            "adapter_class": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
            "input_field": "text",
            "golden_output_field": "summary",
        },
        "extraction": {
            "adapter_class": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
            "input_field": "text",
            "golden_output_field": "extracted_data",
        },
        "custom": {
            "adapter_class": "llama_prompt_ops.core.datasets.ConfigurableJSONAdapter",
            # No default fields - will be populated from user mappings
        },
    }

    def transform(
        self, wizard_data: Dict[str, Any], project_name: str = "generated"
    ) -> Dict[str, Any]:
        """
        Transform onboarding wizard data into YAML configuration.

        Args:
            wizard_data: Data collected from the onboarding wizard
            project_name: Name for the generated project

        Returns:
            Dictionary representing the YAML configuration
        """
        config = {}

        # 1. System Prompt Configuration
        config["system_prompt"] = self._transform_system_prompt(
            wizard_data.get("prompt", {})
        )

        # 2. Dataset Configuration
        config["dataset"] = self._transform_dataset(
            wizard_data.get("dataset", {}), wizard_data.get("useCase")
        )

        # 3. Model Configuration
        config["model"] = self._transform_model(wizard_data.get("models", {}))

        # 4. Metric Configuration
        config["metric"] = self._transform_metric(wizard_data)

        # 5. Optimization Configuration
        config["optimization"] = self._transform_optimization(
            wizard_data.get("optimizer", {})
        )

        return config

    def _transform_system_prompt(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform prompt configuration."""
        config = {
            "inputs": prompt_data.get("inputs", ["question"]),
            "outputs": prompt_data.get("outputs", ["answer"]),
        }

        # Always use file reference for better project structure
        config["file"] = "prompts/prompt.txt"

        return config

    def _transform_dataset(
        self, dataset_data: Dict[str, Any], use_case: str
    ) -> Dict[str, Any]:
        """Transform dataset configuration with support for custom field mappings."""

        # Get base configuration for the use case
        base_config = self.DATASET_FIELD_MAPPING.get(
            use_case, self.DATASET_FIELD_MAPPING["custom"]
        )
        dataset_config = {"adapter_class": base_config["adapter_class"]}

        # Always use standard relative path for project structure
        dataset_config["path"] = "data/dataset.json"

        # Set default train/validation splits (0.5/0.2 as requested)
        dataset_config["train_size"] = dataset_data.get("trainSize", 50) / 100.0
        dataset_config["validation_size"] = (
            dataset_data.get("validationSize", 20) / 100.0
        )

        # Handle field mappings based on use case
        if use_case == "custom":
            # For custom use case, handle flexible field mappings
            field_mappings = dataset_data.get("fieldMappings", {})

            if field_mappings:
                # Find the most likely input and output fields for ConfigurableJSONAdapter
                input_candidates = [
                    "question",
                    "input",
                    "query",
                    "prompt",
                    "text",
                    "user_input",
                ]
                output_candidates = [
                    "answer",
                    "output",
                    "response",
                    "label",
                    "target",
                    "expected_output",
                ]

                input_field = None
                output_field = None

                # Find input field by checking common field name patterns
                for candidate in input_candidates:
                    if candidate in field_mappings and field_mappings[candidate]:
                        input_field = field_mappings[candidate]
                        break

                # Find output field by checking common field name patterns
                for candidate in output_candidates:
                    if candidate in field_mappings and field_mappings[candidate]:
                        output_field = field_mappings[candidate]
                        break

                # Set the detected fields
                if input_field:
                    dataset_config["input_field"] = input_field
                if output_field:
                    dataset_config["golden_output_field"] = output_field

                # Store all custom field mappings for advanced use cases
                dataset_config["custom_field_mappings"] = field_mappings
            else:
                # Fallback to base config if no field mappings
                dataset_config.update(
                    {k: v for k, v in base_config.items() if k != "adapter_class"}
                )

        elif use_case == "rag":
            # RAG-specific field mapping
            field_mappings = dataset_data.get("fieldMappings", {})

            if field_mappings:
                # Map user's field mappings to RAG adapter expected fields
                dataset_config["question_field"] = field_mappings.get(
                    "query", field_mappings.get("question", "query")
                )
                dataset_config["context_field"] = field_mappings.get(
                    "context", "context"
                )
                dataset_config["golden_answer_field"] = field_mappings.get(
                    "answer", "answer"
                )
            else:
                # Use base config defaults
                dataset_config.update(
                    {k: v for k, v in base_config.items() if k != "adapter_class"}
                )

        else:
            # Standard use cases (qa, classification, etc.)
            field_mappings = dataset_data.get("fieldMappings", {})

            if field_mappings:
                # For Q&A and other standard use cases
                dataset_config["input_field"] = field_mappings.get(
                    "question",
                    field_mappings.get(
                        "input", base_config.get("input_field", "question")
                    ),
                )
                dataset_config["golden_output_field"] = field_mappings.get(
                    "answer",
                    field_mappings.get(
                        "output", base_config.get("golden_output_field", "answer")
                    ),
                )
            else:
                # Use base config defaults
                dataset_config.update(
                    {k: v for k, v in base_config.items() if k != "adapter_class"}
                )

        return dataset_config

    def _transform_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform model configuration with full provider support."""
        models = model_data.get("selected", [])

        if not models:
            # Default model configuration (no name field, use task_model/proposer_model)
            return {
                "task_model": "openrouter/meta-llama/llama-3.3-70b-instruct",
                "proposer_model": "openrouter/meta-llama/llama-3.3-70b-instruct",
                "api_base": "https://openrouter.ai/api/v1",
                "temperature": 0.0,
            }

        # Get the primary model configuration
        primary_model = models[0]

        # Build full model name with prefix
        model_prefix = primary_model.get("model_prefix", "")
        model_name = primary_model.get("model_name", "")
        full_model_name = f"{model_prefix}{model_name}" if model_prefix else model_name

        # Start with base model configuration (no name field)
        model_config = {}

        # Add API base if provided
        if primary_model.get("api_base"):
            model_config["api_base"] = primary_model["api_base"]

        # Add generation parameters
        if "temperature" in primary_model:
            model_config["temperature"] = primary_model["temperature"]
        if "max_tokens" in primary_model:
            model_config["max_tokens"] = primary_model["max_tokens"]

        # Handle multiple models with different roles
        target_models = [m for m in models if m.get("role") in ["target", "both"]]
        optimizer_models = [m for m in models if m.get("role") in ["optimizer", "both"]]

        if target_models and optimizer_models and len(models) > 1:
            # Separate target and optimizer models
            target_model = target_models[0]
            optimizer_model = optimizer_models[0]

            target_prefix = target_model.get("model_prefix", "")
            target_name = target_model.get("model_name", "")
            target_full_name = (
                f"{target_prefix}{target_name}" if target_prefix else target_name
            )

            optimizer_prefix = optimizer_model.get("model_prefix", "")
            optimizer_name = optimizer_model.get("model_name", "")
            optimizer_full_name = (
                f"{optimizer_prefix}{optimizer_name}"
                if optimizer_prefix
                else optimizer_name
            )

            # Only set task_model and proposer_model (no name field)
            model_config.update(
                {
                    "task_model": target_full_name,
                    "proposer_model": optimizer_full_name,
                }
            )
        else:
            # Single model for both tasks (no name field)
            model_config.update(
                {
                    "task_model": full_model_name,
                    "proposer_model": full_model_name,
                }
            )

        return model_config

    def _transform_metric(self, wizard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform metric configuration using actual selected metrics."""

        # Get selected metrics from wizard data
        selected_metrics = wizard_data.get("metrics", [])
        metric_configurations = wizard_data.get("metricConfigurations", {})

        # If no metrics selected, fall back to use case default
        if not selected_metrics:
            use_case = wizard_data.get("useCase", "custom")
            fallback_metric_id = self.USE_CASE_FALLBACK_METRICS.get(
                use_case, "exact_match"
            )
            selected_metrics = [fallback_metric_id]

        # Use the first selected metric (for now, could be enhanced for multiple metrics)
        primary_metric_id = selected_metrics[0]

        # Get metric configuration from mapping
        metric_mapping = self.METRIC_ID_MAPPING.get(primary_metric_id)
        if not metric_mapping:
            # Fallback to exact match if unknown metric
            metric_mapping = self.METRIC_ID_MAPPING["exact_match"]

        # Start with base metric configuration
        metric_config = {"class": metric_mapping["class"]}

        # Add default parameters for this metric type
        metric_config.update(metric_mapping["default_params"])

        # Add user-configured parameters if available
        if primary_metric_id in metric_configurations:
            user_config = metric_configurations[primary_metric_id]
            metric_config.update(user_config)

        # Determine output field from field mappings
        dataset_data = wizard_data.get("dataset", {})
        field_mappings = dataset_data.get("fieldMappings", {})

        if field_mappings:
            # Find the actual output field from field mappings
            output_candidates = [
                "answer",
                "output",
                "response",
                "label",
                "target",
                "expected_output",
            ]

            for candidate in output_candidates:
                if candidate in field_mappings and field_mappings[candidate]:
                    metric_config["output_fields"] = [
                        candidate  # Use the target field name
                    ]
                    break

        # Ensure output_fields is set (fallback to ["answer"])
        if "output_fields" not in metric_config:
            metric_config["output_fields"] = ["answer"]

        return metric_config

    def _transform_optimization(self, optimizer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform optimization configuration using only frontend-controlled parameters."""
        strategy_id = optimizer_data.get("selectedOptimizer", "basic")
        custom_params = optimizer_data.get("customParams", {})

        optimization_config = {"strategy": strategy_id}

        # Add frontend-controlled parameters if provided
        if custom_params:
            # Only include parameters that are actually controlled by the frontend
            frontend_controlled_params = {
                "num_candidates": "num_candidates",
                "max_bootstrapped_demos": "bootstrap_examples",
                "max_labeled_demos": "max_labeled_demos",
                "num_threads": "num_threads",
                "max_errors": "max_errors",
                "seed": "seed",
            }

            for frontend_key, backend_key in frontend_controlled_params.items():
                if frontend_key in custom_params:
                    optimization_config[backend_key] = custom_params[frontend_key]

        return optimization_config

    def _extract_environment_variables(
        self, wizard_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract API keys and other sensitive data for .env file."""
        env_vars = {}

        models = wizard_data.get("models", {}).get("selected", [])

        for model in models:
            api_key = model.get("api_key")
            provider_id = model.get("provider_id")

            if api_key and api_key.strip():
                # Create environment variable name based on provider
                env_var_name = f"{provider_id.upper()}_API_KEY"
                env_vars[env_var_name] = api_key

        return env_vars

    def generate_yaml_string(
        self, wizard_data: Dict[str, Any], project_name: str = "generated"
    ) -> str:
        """
        Generate YAML configuration string from wizard data.

        Args:
            wizard_data: Data collected from the onboarding wizard
            project_name: Name for the generated project

        Returns:
            YAML configuration as string
        """
        config = self.transform(wizard_data, project_name)
        return yaml.dump(config, default_flow_style=False, sort_keys=False)

    def save_config_file(
        self,
        wizard_data: Dict[str, Any],
        output_path: str,
        project_name: str = "generated",
    ) -> str:
        """
        Save YAML configuration file from wizard data.

        Args:
            wizard_data: Data collected from the onboarding wizard
            output_path: Path where to save the config file
            project_name: Name for the generated project

        Returns:
            Path to the saved configuration file
        """
        config = self.transform(wizard_data, project_name)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        return output_path

    def create_project_structure(
        self, wizard_data: Dict[str, Any], base_dir: str, project_name: str
    ) -> Dict[str, str]:
        """
        Create complete project structure with all necessary files.

        Args:
            wizard_data: Data collected from the onboarding wizard
            base_dir: Base directory where to create the project
            project_name: Name of the project

        Returns:
            Dictionary mapping file types to their created paths
        """
        project_dir = os.path.join(base_dir, project_name)
        created_files = {}

        # Create directory structure
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, "data"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "prompts"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "results"), exist_ok=True)

        # 1. Create config.yaml
        config_path = os.path.join(project_dir, "config.yaml")
        self.save_config_file(wizard_data, config_path, project_name)
        created_files["config"] = config_path

        # 2. Create prompt file
        prompt_path = os.path.join(project_dir, "prompts", "prompt.txt")
        prompt_text = wizard_data.get("prompt", {}).get(
            "text", "# Add your system prompt here"
        )
        with open(prompt_path, "w") as f:
            f.write(prompt_text)
        created_files["prompt"] = prompt_path

        # 3. Copy uploaded dataset file to standard location
        dataset_path = os.path.join(project_dir, "data", "dataset.json")

        # Get the uploaded dataset path from wizard data
        uploaded_dataset_path = wizard_data.get("dataset", {}).get("path")

        if uploaded_dataset_path and os.path.exists(uploaded_dataset_path):
            # Copy the actual uploaded file
            import shutil

            shutil.copy2(uploaded_dataset_path, dataset_path)
        else:
            # Fallback to placeholder data if no uploaded file found
            placeholder_data = self._create_placeholder_dataset(
                wizard_data.get("useCase", "custom")
            )
            with open(dataset_path, "w") as f:
                import json

                json.dump(placeholder_data, f, indent=2)

        created_files["dataset"] = dataset_path

        # 4. Create .env file with actual API keys
        env_path = os.path.join(project_dir, ".env")
        env_vars = self._extract_environment_variables(wizard_data)

        env_content = "# API Keys\n"
        if env_vars:
            for var_name, var_value in env_vars.items():
                env_content += f"{var_name}={var_value}\n"
        else:
            env_content += "# Add your API keys here\n"
            env_content += "# OPENROUTER_API_KEY=your_api_key_here\n"
            env_content += "# ANTHROPIC_API_KEY=your_api_key_here\n"

        with open(env_path, "w") as f:
            f.write(env_content)
        created_files["env"] = env_path

        # 5. Create README.md
        readme_path = os.path.join(project_dir, "README.md")
        readme_content = self._create_readme(project_name, wizard_data)
        with open(readme_path, "w") as f:
            f.write(readme_content)
        created_files["readme"] = readme_path

        return created_files

    def _create_placeholder_dataset(self, use_case: str) -> List[Dict[str, Any]]:
        """Create a placeholder dataset based on use case."""
        datasets = {
            "qa": [
                {
                    "question": "What is artificial intelligence?",
                    "answer": "AI is the simulation of human intelligence in machines.",
                },
                {
                    "question": "How does machine learning work?",
                    "answer": "Machine learning uses algorithms to learn patterns from data.",
                },
                {
                    "question": "What is deep learning?",
                    "answer": "Deep learning uses neural networks with multiple layers.",
                },
                {
                    "question": "What are the benefits of AI?",
                    "answer": "AI can automate tasks, provide insights, and improve efficiency.",
                },
            ],
            "rag": [
                {
                    "question": "What is the capital of France?",
                    "context": "France is a country in Europe. Its capital city is Paris.",
                    "answer": "Paris",
                },
                {
                    "question": "Who wrote Romeo and Juliet?",
                    "context": "William Shakespeare was an English playwright and poet. He wrote many famous plays including Romeo and Juliet.",
                    "answer": "William Shakespeare",
                },
                {
                    "question": "What is photosynthesis?",
                    "context": "Photosynthesis is the process by which plants use sunlight, water and carbon dioxide to produce oxygen and energy.",
                    "answer": "The process by which plants convert sunlight into energy",
                },
                {
                    "question": "When was the internet invented?",
                    "context": "The internet was developed in the late 1960s as ARPANET by DARPA. The World Wide Web was created by Tim Berners-Lee in 1989.",
                    "answer": "Late 1960s (ARPANET), World Wide Web in 1989",
                },
            ],
            "classification": [
                {
                    "text": "I love this product! It works perfectly.",
                    "category": "positive",
                },
                {
                    "text": "This is terrible quality and broke immediately.",
                    "category": "negative",
                },
                {
                    "text": "The product is okay, nothing special but functional.",
                    "category": "neutral",
                },
                {"text": "Amazing service and fast delivery!", "category": "positive"},
            ],
            "summarization": [
                {
                    "text": "The meeting covered quarterly sales figures, upcoming product launches, and budget allocations for the next fiscal year. Sales exceeded expectations by 15% and three new products will launch in Q2.",
                    "summary": "Meeting discussed Q1 sales (15% above target), Q2 product launches, and budget planning.",
                },
                {
                    "text": "Research shows that exercise improves mental health, reduces stress, and increases cognitive function. Regular physical activity releases endorphins and promotes better sleep patterns.",
                    "summary": "Exercise benefits mental health through endorphin release, stress reduction, and improved cognition and sleep.",
                },
                {
                    "text": "The new software update includes bug fixes, security improvements, and user interface enhancements. Performance has been optimized and several new features added based on user feedback.",
                    "summary": "Software update includes bug fixes, security improvements, UI enhancements, and performance optimizations.",
                },
                {
                    "text": "Climate change is causing rising sea levels, extreme weather events, and ecosystem disruption. Scientists recommend immediate action to reduce greenhouse gas emissions.",
                    "summary": "Climate change causes rising seas, extreme weather, and ecosystem damage. Scientists urge immediate emission reductions.",
                },
            ],
        }

        return datasets.get(
            use_case,
            [
                {"fields": {"input": "Example input"}, "answer": "Example output"},
                {"fields": {"input": "Another input"}, "answer": "Another output"},
                {"fields": {"input": "Third input"}, "answer": "Third output"},
                {"fields": {"input": "Fourth input"}, "answer": "Fourth output"},
            ],
        )

    def _create_readme(self, project_name: str, wizard_data: Dict[str, Any]) -> str:
        """Create README.md content for the project."""
        use_case = wizard_data.get("useCase", "custom")
        optimizer = wizard_data.get("optimizer", {}).get("selectedOptimizer", "basic")

        return f"""# {project_name}

## Project Overview

This project was generated using the llama-prompt-ops onboarding wizard.

**Use Case:** {use_case.title()}
**Optimization Strategy:** {optimizer.title()}

## Project Structure

```
{project_name}/
├── config.yaml          # Main configuration file
├── prompts/
│   └── prompt.txt       # System prompt template
├── data/
│   └── dataset.json     # Training dataset
├── results/             # Optimization results
└── .env                 # Environment variables (API keys)
```

## Getting Started

1. **Set up your API key:**
   ```bash
   # Edit .env file and add your API key
   OPENROUTER_API_KEY=your_actual_api_key_here
   ```

2. **Install llama-prompt-ops:**
   ```bash
   pip install llama-prompt-ops
   ```

3. **Customize your prompt:**
   Edit `prompts/prompt.txt` with your actual system prompt.

4. **Add your dataset:**
   Replace the placeholder data in `data/dataset.json` with your actual dataset.

5. **Run optimization:**
   ```bash
   prompt-ops migrate --config config.yaml
   ```

## Configuration

The `config.yaml` file contains all the settings for your optimization run:

- **system_prompt**: Path to your prompt file and input/output specifications
- **dataset**: Dataset path and field mappings
- **model**: AI models to use for optimization
- **metric**: Evaluation metric for measuring prompt performance
- **optimization**: Strategy and parameters for optimization

## Next Steps

1. Customize the system prompt in `prompts/prompt.txt`
2. Replace placeholder dataset with your actual data
3. Review and adjust configuration parameters
4. Run the optimization and analyze results

## Support

For more information, see the [llama-prompt-ops documentation](https://github.com/meta-llama/llama-prompt-ops).
"""
