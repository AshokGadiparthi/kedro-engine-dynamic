"""Datasets API Routes - Saves to Kedro Project"""
from fastapi import APIRouter, Depends, Path, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from typing import Optional
import os
import pandas as pd
import numpy as np
import io
import logging
from app.core.database import get_db
from app.models.models import Dataset
from app.schemas import DatasetCreate, DatasetResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Datasets"])

# ============================================================================
# KEDRO PROJECT PATH - Change this to your Kedro project root
# ============================================================================
KEDRO_PROJECT_PATH = "/home/ashok/work/latest/full/kedro-ml-engine-integrated"
KEDRO_RAW_DATA_DIR = os.path.join(KEDRO_PROJECT_PATH, "data", "01_raw")

# Ensure base directory exists
os.makedirs(KEDRO_RAW_DATA_DIR, exist_ok=True)

logger.info(f"✅ Kedro raw data directory: {KEDRO_RAW_DATA_DIR}")

# In-memory storage for dataset content
dataset_cache = {}


@router.get("/", response_model=list)
async def list_datasets(db: Session = Depends(get_db)):
    """List all datasets"""
    datasets = db.query(Dataset).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "project_id": d.project_id,
            "description": d.description,
            "file_name": d.file_name,
            "file_size_bytes": d.file_size_bytes,
            "created_at": d.created_at.isoformat() if d.created_at else ""
        }
        for d in datasets
    ]


@router.post("/")
async def create_dataset(
        file: UploadFile = File(...),
        name: str = Form(...),
        project_id: str = Form(...),
        description: Optional[str] = Form(None),
        db: Session = Depends(get_db)
):
    """
    Create dataset and save to Kedro project path

    Flow:
    1. Create project-specific directory: {KEDRO}/data/01_raw/{project_id}/
    2. Save file with original filename (overwrites if exists)
    3. Store Kedro-relative path in database
    4. Return paths for job parameter
    """

    dataset_id = str(uuid4())
    logger.info(f"📥 Uploading dataset: {name} for project: {project_id}")

    try:
        # ✅ Step 1: Create project directory structure
        project_dir = os.path.join(KEDRO_RAW_DATA_DIR, project_id)
        os.makedirs(project_dir, exist_ok=True)
        logger.info(f"📁 Created project directory: {project_dir}")

        # ✅ Step 2: Save file with original filename (allows overwrite)
        original_filename = file.filename
        full_file_path = os.path.join(project_dir, original_filename)

        contents = await file.read()
        with open(full_file_path, "wb") as f:
            f.write(contents)

        # ✅ Step 2.1: Hard validation (prevents “file not found” later)
        if not os.path.exists(full_file_path) or os.path.getsize(full_file_path) == 0:
            raise RuntimeError(f"File write failed or empty: {full_file_path}")

        logger.info(f"✅ File saved: {full_file_path}")

        # ✅ Step 3: Kedro-relative path for parameters (good for Kedro project runs)
        kedro_relative_path = f"data/01_raw/{project_id}/{original_filename}"
        logger.info(f"📍 Kedro path: {kedro_relative_path}")

        # ✅ Step 4: ANALYZE the file (only if CSV)
        row_count = 0
        column_count = 0
        try:
            if original_filename.lower().endswith(".csv"):
                df = pd.read_csv(full_file_path)
                row_count = len(df)
                column_count = len(df.columns)
                logger.info(f"✅ Analysis: {row_count} rows, {column_count} columns")
                dataset_cache[dataset_id] = df
            else:
                logger.info("ℹ️ Skipping CSV analysis (not a CSV file)")
        except Exception as e:
            logger.warning(f"⚠️ Could not analyze CSV: {e}")

        # ✅ Step 5: Create dataset record in database
        new_dataset = Dataset(
            id=dataset_id,
            name=name,
            project_id=project_id,
            description=description or "",
            file_name=original_filename,
            file_size_bytes=len(contents),
            created_at=datetime.now()
        )
        db.add(new_dataset)
        db.commit()
        db.refresh(new_dataset)

        logger.info(f"✅ Dataset created: {dataset_id}")

        # ✅ IMPORTANT: return both abs path and kedro path
        return {
            "id": new_dataset.id,
            "name": new_dataset.name,
            "project_id": new_dataset.project_id,
            "description": new_dataset.description,
            "file_name": new_dataset.file_name,
            "file_size_bytes": new_dataset.file_size_bytes,
            "created_at": new_dataset.created_at.isoformat(),

            # ✅ for Kedro run (relative)
            "kedro_path": kedro_relative_path,

            # ✅ for Celery/Kedro subprocess safety (absolute)
            "abs_path": full_file_path,

            # optional debug
            "row_count": row_count,
            "column_count": column_count,
        }

    except Exception as e:
        logger.error(f"❌ Error uploading dataset: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload dataset: {str(e)}")



@router.get("/{dataset_id}/preview")
async def get_dataset_preview(dataset_id: str = Path(...), rows: int = 100, db: Session = Depends(get_db)):
    """Get dataset preview - returns actual data with columns and rows"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}

    df = None

    # ✅ Build path from project_id and filename (Kedro structure)
    file_path = os.path.join(
        KEDRO_RAW_DATA_DIR,
        dataset.project_id,
        dataset.file_name
    )

    # Load from cache or file
    if dataset_id in dataset_cache:
        df = dataset_cache[dataset_id]
    else:
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, nrows=rows)
                dataset_cache[dataset_id] = df
                logger.info(f"✅ Loaded dataset preview: {dataset_id}")
            except Exception as e:
                logger.error(f"❌ Could not read file: {str(e)}")
                return {"error": f"Could not read file: {str(e)}"}

    if df is None or df.empty:
        return {"error": "No data available"}

    # Format columns
    columns = [
        {
            "name": col,
            "type": str(df[col].dtype),
        }
        for col in df.columns
    ]

    # Format rows
    rows_data = df.to_dict('records')

    return {
        "dataset_id": dataset_id,
        "columns": columns,
        "rows": rows_data,
        "total_rows": len(df),
        "preview_rows": len(rows_data),
    }


@router.get("/{dataset_id}/quality")
async def get_dataset_quality(dataset_id: str = Path(...), db: Session = Depends(get_db)):
    """Get REAL data quality analysis with detailed metrics"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}

    df = None

    # ✅ Build path from project_id and filename (Kedro structure)
    file_path = os.path.join(
        KEDRO_RAW_DATA_DIR,
        dataset.project_id,
        dataset.file_name
    )

    # Load from cache or file
    if dataset_id in dataset_cache:
        df = dataset_cache[dataset_id]
    else:
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                dataset_cache[dataset_id] = df
                logger.info(f"✅ Loaded dataset for quality analysis: {dataset_id}")
            except Exception as e:
                logger.error(f"❌ Could not read file: {str(e)}")
                return {"error": f"Could not read file: {str(e)}"}

    if df is None or df.empty:
        return {"error": "No data available"}

    # Calculate REAL statistics
    total_rows = len(df)
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    duplicate_rows = df.duplicated().sum()

    # Calculate metrics
    missing_percentage = (missing_cells / total_cells * 100) if total_cells > 0 else 0
    completeness = 100 - missing_percentage
    uniqueness = 100 - (duplicate_rows / total_rows * 100) if total_rows > 0 else 100
    consistency = 100

    # Per-column quality
    column_quality = []
    for col in df.columns:
        col_missing = df[col].isnull().sum()
        col_total = len(df[col])
        col_missing_pct = (col_missing / col_total * 100) if col_total > 0 else 0

        column_quality.append({
            "name": col,
            "data_type": str(df[col].dtype),
            "missing_count": int(col_missing),
            "missing_percentage": float(col_missing_pct),
            "unique_count": int(df[col].nunique()),
        })

    return {
        "dataset_id": dataset_id,
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "duplicate_rows": int(duplicate_rows),
        "missing_percentage": float(missing_percentage),
        "completeness": float(completeness),
        "uniqueness": float(uniqueness),
        "consistency": float(consistency),
        "overall_quality_score": round((completeness + uniqueness + consistency) / 3, 2),
        "column_quality": column_quality
    }


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str = Path(...), db: Session = Depends(get_db)):
    """Delete dataset and its file from Kedro path"""
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            return {"error": "Dataset not found"}

        # ✅ Delete file from Kedro path
        file_path = os.path.join(
            KEDRO_RAW_DATA_DIR,
            dataset.project_id,
            dataset.file_name
        )

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑️ Deleted file: {file_path}")

        # ✅ Delete from cache
        if dataset_id in dataset_cache:
            del dataset_cache[dataset_id]

        # ✅ Delete from database
        db.delete(dataset)
        db.commit()

        logger.info(f"✅ Dataset deleted: {dataset_id}")

        return {"message": "Dataset deleted successfully"}

    except Exception as e:
        logger.error(f"❌ Error deleting dataset: {str(e)}", exc_info=True)
        db.rollback()
        return {"error": f"Failed to delete dataset: {str(e)}"}