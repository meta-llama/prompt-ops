"""
Project creation and management endpoints.
"""

import logging
import os
from typing import Any, Dict

from config import UPLOAD_DIR
from config_transformer import ConfigurationTransformer
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from utils import generate_unique_project_name

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models
class QuickStartResponse(BaseModel):
    success: bool
    dataset: Dict[str, Any]
    prompt: str
    config: Dict[str, Any]
    message: str


@router.post("/api/quick-start-demo", response_model=QuickStartResponse)
async def quick_start_demo():
    """Load the facility support analyzer demo with dataset, prompt, and optimal configuration."""
    try:
        # Define paths to demo files
        demo_dataset_path = os.path.join(
            os.path.dirname(__file__),
            "..",
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

        import shutil

        shutil.copy2(demo_dataset_path, destination_path)

        # Load and validate the dataset
        import json

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
            "metrics": "Exact Match",  # Temporarily use simpler metric for debugging
            "model": "Llama 3.3 70B",
            "proposer": "Llama 3.3 70B",
            "strategy": "Basic",
            "useLlamaTips": True,
        }

        # Create dataset response
        dataset_response = {
            "filename": demo_filename,
            "path": destination_path,
            "preview": preview,
            "total_records": len(data),
        }

        logger.info(f"Quick start demo loaded successfully: {len(data)} records")

        return QuickStartResponse(
            success=True,
            dataset=dataset_response,
            prompt=demo_prompt,
            config=optimal_config,
            message=f"Demo loaded successfully! Facility Support Analyzer with {len(data)} sample records ready for optimization.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading quick start demo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load demo: {str(e)}")


@router.post("/generate-config")
async def generate_config(request: dict):
    """Generate YAML configuration from onboarding wizard data."""
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
            uploads_dir = UPLOAD_DIR
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


@router.post("/create-project")
async def create_project(request: dict):
    """Create a complete project structure with config, prompt, and dataset files."""
    try:
        wizard_data = request.get("wizardData", {})
        requested_project_name = request.get("projectName", "generated-project")

        # Create project in uploads directory
        uploads_dir = UPLOAD_DIR

        # Generate unique project name to avoid conflicts
        unique_project_name = generate_unique_project_name(
            requested_project_name, uploads_dir
        )
        logger.info(f"Requested project name: {requested_project_name}")
        logger.info(f"Using unique project name: {unique_project_name}")

        # Fix dataset path to point to actual uploaded file
        dataset_info = wizard_data.get("dataset", {})
        if "path" in dataset_info:
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
            "actualProjectName": unique_project_name,
            "requestedProjectName": requested_project_name,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/download-config/{project_name}")
async def download_config(project_name: str):
    """Download the config.yaml file for a generated project."""
    try:
        uploads_dir = UPLOAD_DIR
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
