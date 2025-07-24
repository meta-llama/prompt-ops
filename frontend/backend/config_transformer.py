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

    # Mapping from wizard use cases to optimal metric configurations
    METRIC_MAPPING = {
        "qa": {
            "class": "llama_prompt_ops.core.metrics.ExactMatchMetric",
            "output_field": "answer",
        },
        "rag": {
            "class": "llama_prompt_ops.core.metrics.FacilityMetric",
            "strict_json": False,
            "output_field": "answer",
        },
        "classification": {
            "class": "llama_prompt_ops.core.metrics.ExactMatchMetric",
            "output_field": "category",
        },
        "summarization": {
            "class": "llama_prompt_ops.core.metrics.FacilityMetric",
            "strict_json": False,
            "output_field": "summary",
        },
        "extraction": {
            "class": "llama_prompt_ops.core.metrics.StandardJSONMetric",
            "output_field": "extracted_data",
        },
        "custom": {
            "class": "llama_prompt_ops.core.metrics.FacilityMetric",
            "strict_json": False,
            "output_field": "answer",
        },
    }

    # Mapping from wizard dataset types to input/output field configurations
    DATASET_FIELD_MAPPING = {
        "qa": {"input_field": "question", "golden_output_field": "answer"},
        "rag": {
            "input_field": ["question", "context"],
            "golden_output_field": "answer",
        },
        "classification": {"input_field": "text", "golden_output_field": "category"},
        "summarization": {"input_field": "text", "golden_output_field": "summary"},
        "extraction": {"input_field": "text", "golden_output_field": "extracted_data"},
        "custom": {"input_field": ["fields", "input"], "golden_output_field": "answer"},
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
        config["metric"] = self._transform_metric(
            wizard_data.get("useCase"), wizard_data.get("dataset", {})
        )

        # 5. Optimization Configuration
        config["optimization"] = self._transform_optimization(
            wizard_data.get("optimizer", {})
        )

        return config

    def _transform_system_prompt(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform prompt configuration."""
        # Default to file-based prompt storage
        return {
            "file": "prompts/prompt.txt",
            "inputs": prompt_data.get("inputs", ["question"]),
            "outputs": prompt_data.get("outputs", ["answer"]),
        }

    def _transform_dataset(
        self, dataset_data: Dict[str, Any], use_case: str
    ) -> Dict[str, Any]:
        """Transform dataset configuration."""
        dataset_config = {"path": "data/dataset.json"}

        # Get field mapping based on use case
        field_mapping = self.DATASET_FIELD_MAPPING.get(
            use_case, self.DATASET_FIELD_MAPPING["custom"]
        )
        dataset_config.update(field_mapping)

        # Add custom field mappings if provided
        if "inputField" in dataset_data:
            dataset_config["input_field"] = dataset_data["inputField"]
        if "outputField" in dataset_data:
            dataset_config["golden_output_field"] = dataset_data["outputField"]

        # Add dataset splits if configured
        if "trainSize" in dataset_data:
            dataset_config["train_size"] = dataset_data["trainSize"] / 100.0
        if "validationSize" in dataset_data:
            dataset_config["validation_size"] = dataset_data["validationSize"] / 100.0

        return dataset_config

    def _transform_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform model configuration."""
        models = model_data.get("selected", [])

        if not models:
            # Default model
            default_model = "openrouter/meta-llama/llama-3.3-70b-instruct"
            return {"task_model": default_model, "proposer_model": default_model}

        # Use first selected model for both task and proposer if only one selected
        if len(models) == 1:
            model_name = models[0]["name"]
            return {"task_model": model_name, "proposer_model": model_name}

        # Use separate models if multiple selected
        return {
            "task_model": models[0]["name"],
            "proposer_model": (
                models[1]["name"] if len(models) > 1 else models[0]["name"]
            ),
        }

    def _transform_metric(
        self, use_case: str, dataset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform metric configuration."""
        metric_config = self.METRIC_MAPPING.get(
            use_case, self.METRIC_MAPPING["custom"]
        ).copy()

        # Override output field if custom field mapping provided
        if "outputField" in dataset_data:
            metric_config["output_field"] = dataset_data["outputField"]

        return metric_config

    def _transform_optimization(self, optimizer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform optimization configuration."""
        strategy_id = optimizer_data.get("selectedOptimizer", "basic")
        custom_params = optimizer_data.get("customParams", {})

        optimization_config = {}

        # Set strategy type
        if strategy_id == "llama":
            optimization_config["strategy"] = "llama"

            # Add Llama-specific parameters
            optimization_config.update(
                {
                    "apply_formatting": True,
                    "apply_templates": True,
                    "template_type": "basic",
                }
            )
        else:
            optimization_config["strategy"] = "basic"

        # Add custom parameters if provided
        if custom_params:
            # Map frontend parameter names to backend names
            param_mapping = {
                "num_candidates": "num_candidates",
                "max_bootstrapped_demos": "max_bootstrapped_demos",
                "max_labeled_demos": "max_labeled_demos",
                "num_threads": "num_threads",
                "max_errors": "max_errors",
                "seed": "seed",
            }

            for frontend_key, backend_key in param_mapping.items():
                if frontend_key in custom_params:
                    optimization_config[backend_key] = custom_params[frontend_key]

        return optimization_config

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

        # 3. Create placeholder dataset file
        dataset_path = os.path.join(project_dir, "data", "dataset.json")
        placeholder_data = self._create_placeholder_dataset(
            wizard_data.get("useCase", "custom")
        )
        with open(dataset_path, "w") as f:
            import json

            json.dump(placeholder_data, f, indent=2)
        created_files["dataset"] = dataset_path

        # 4. Create .env file
        env_path = os.path.join(project_dir, ".env")
        env_content = "# API Keys\nOPENROUTER_API_KEY=your_api_key_here\n"
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
