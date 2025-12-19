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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading config for project {project_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects")
async def list_projects():
    """List all available projects in the uploads directory."""
    try:
        uploads_dir = UPLOAD_DIR

        # Return empty list if directory doesn't exist yet
        if not os.path.exists(uploads_dir):
            return {"success": True, "projects": []}

        projects = []

        # List all directories in the uploads folder
        for item in os.listdir(uploads_dir):
            item_path = os.path.join(uploads_dir, item)

            # Only include directories (skip individual files)
            if os.path.isdir(item_path):
                config_path = os.path.join(item_path, "config.yaml")
                prompt_path = os.path.join(item_path, "prompts", "prompt.txt")
                dataset_path = os.path.join(item_path, "data", "dataset.json")

                # Get creation/modification time
                created_at = os.path.getctime(item_path)
                modified_at = os.path.getmtime(item_path)

                project_info = {
                    "name": item,
                    "path": item_path,
                    "hasConfig": os.path.exists(config_path),
                    "hasPrompt": os.path.exists(prompt_path),
                    "hasDataset": os.path.exists(dataset_path),
                    "createdAt": created_at,
                    "modifiedAt": modified_at,
                }

                projects.append(project_info)

        # Sort by modification time (most recent first)
        projects.sort(key=lambda x: x["modifiedAt"], reverse=True)

        logger.info(f"Found {len(projects)} projects")
        return {"success": True, "projects": projects}

    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list projects: {str(e)}"
        )
