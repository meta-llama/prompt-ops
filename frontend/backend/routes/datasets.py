"""
Dataset upload, analysis, and management endpoints.
"""

import json
import logging
import os
from typing import Any, Dict

from config import UPLOAD_DIR
from dataset_analyzer import DatasetAnalyzer
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from utils import get_uploaded_datasets

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize dataset analyzer
dataset_analyzer = DatasetAnalyzer()


# Pydantic models for this module
class DatasetUploadResponse(BaseModel):
    filename: str
    path: str
    preview: list[Dict[str, Any]]
    total_records: int


class DatasetListResponse(BaseModel):
    datasets: list[Dict[str, Any]]


class DatasetAnalysisResponse(BaseModel):
    total_records: int
    sample_size: int
    fields: list[Dict[str, Any]]
    suggestions: Dict[str, Any]
    sample_data: list[Dict[str, Any]]
    error: str = None


class FieldMappingRequest(BaseModel):
    filename: str
    mappings: Dict[str, str]
    use_case: str


class PreviewTransformationRequest(BaseModel):
    filename: str
    mappings: Dict[str, str]
    use_case: str


class PreviewTransformationResponse(BaseModel):
    original_data: list[Dict[str, Any]]
    transformed_data: list[Dict[str, Any]]
    adapter_config: Dict[str, Any]
    error: str = None


@router.post("/api/datasets/upload", response_model=DatasetUploadResponse)
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
        raise
    except Exception as e:
        logger.error(f"Error uploading dataset: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to upload dataset: {str(e)}"
        )


@router.get("/api/datasets", response_model=DatasetListResponse)
async def list_datasets():
    """List all uploaded datasets."""
    return {"datasets": get_uploaded_datasets()}


@router.delete("/api/datasets/{filename}")
async def delete_dataset(filename: str):
    """Delete an uploaded dataset."""
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        os.remove(file_path)
        return {"message": f"Dataset {filename} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting dataset {filename}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete dataset: {str(e)}"
        )


@router.post("/api/datasets/analyze/{filename}", response_model=DatasetAnalysisResponse)
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
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze dataset: {str(e)}"
        )


@router.post(
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
        raise HTTPException(
            status_code=500, detail=f"Failed to preview transformation: {str(e)}"
        )


@router.post("/api/datasets/save-mapping")
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
        raise HTTPException(
            status_code=500, detail=f"Failed to save field mapping: {str(e)}"
        )
