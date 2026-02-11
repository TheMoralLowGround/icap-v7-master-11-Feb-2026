"""
RabbitMQ handler for preprocess service.

This module contains handler functions for processing preprocess tasks.
All async API callbacks have been replaced with RabbitMQ message publishing.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import concurrent.futures
from producer import publish

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.dense_page_detector.app import detect_dense_pages
from services.detect_pdf import is_electronic_pdf
from services.electronic_pdf import process_files

logger = logging.getLogger(__name__)


def ignore_dense_pages_task(data: dict) -> Dict[str, Any]:
    """
    Task to detect dense pages in image directories
    """
    job_id = data.get("job_id")
    attachments_folder = data.get("attachments_folder")
    batch_id = data.get("batch_id")
    train_batch_log = data.get("train_batch_log")
        
    try:
        logger.info("Ignore Dense Pages Task Started")
        
        image_dir_paths = data.get("image_dir_paths", [])
        
        if not image_dir_paths:
            error = "image_dir_paths not found."
            logger.error(f"{error=}")
            result = {"error": error, "status_code": 400}
            publish('ignore_dense_pages_response', 'to_pipeline', result)
            return
        
        image_dir_paths = [Path(p) for p in image_dir_paths]
        
        dense_pages_list = detect_dense_pages(
            img_folders=image_dir_paths
        )
        
        response = {
            "dense_pages_list": dense_pages_list,
            "status_code": 200,
            "job_id": job_id,
            "attachments_folder": attachments_folder,
            "batch_id": batch_id,
            "train_batch_log": train_batch_log
        }
        logger.info(f"Task completed: {len(dense_pages_list)} dense pages found")
        
        # Always publish result to RabbitMQ
        publish('ignore_dense_pages_response', 'to_pipeline', response)
        
    except Exception as e:
        logger.error(f"Error in ignore_dense_pages_task: {e}")
        result = {"error": str(e), "status_code": 500}
        publish('ignore_dense_pages_response', 'to_pipeline', result)


def categorize_pdfs_task(data: dict) -> Dict[str, Any]:
    """
    Task to check if a PDF is electronic or scanned
    """
    job_id = data.get("job_id")
    
    try:
        logger.info("Is Electronic PDF Task Started")
        
        pdf_paths = data.get("pdf_paths")
        
        if not pdf_paths:
            error = "pdf_paths not found."
            logger.error(f"{error=}")
            result = {"error": error, "status_code": 400}
            publish('pdf_categorization_response', 'to_pipeline', result)
            return
        
        pdf_paths = [Path(p) for p in pdf_paths]
        
        if not all(pdf_path.exists() for pdf_path in pdf_paths):
            error = f"PDF file not found: {pdf_paths}"
            logger.error(f"{error=}")
            result = {"error": error, "status_code": 400}
            publish('pdf_categorization_response', 'to_pipeline', result)
            return
        
        # Call is_electronic_pdf in parallel for each PDF path
        categorization_results = {}
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all tasks
            future_to_pdf_path = {
                executor.submit(is_electronic_pdf, str(pdf_path)): pdf_path 
                for pdf_path in pdf_paths
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_pdf_path):
                pdf_path = future_to_pdf_path[future]
                try:
                    is_electronic = future.result()
                    categorization_results[str(pdf_path)] = {
                        "is_electronic": is_electronic
                    }
                except Exception as e:
                    logger.error(f"Error processing PDF {pdf_path}: {e}")
                    categorization_results[str(pdf_path)] = {
                        "is_electronic": False,
                        "error": str(e)
                    }
        
        response = {
            "categorization_results": categorization_results,
            "status_code": 200,
            "job_id": job_id
        }
        logger.info(f"Task completed: Processed {len(pdf_paths)} PDFs")
        
        # Always publish result to RabbitMQ
        publish('pdf_categorization_response', 'to_pipeline', response)
        
    except Exception as e:
        logger.error(f"Error in categorize_pdfs_task: {e}")
        result = {"error": str(e), "status_code": 500}
        publish('pdf_categorization_response', 'to_pipeline', result)


def process_files_task(data: dict) -> Dict[str, Any]:
    """
    Task to process PDF files and combine them into RAJson output
    """
    job_id = data.get("job_id")
    
    try:
        logger.info("Process Files Task Started")
        
        # Get job info from Redis
        from utils.redis import redis_instance
        import json
        
        job_info_str = redis_instance.get(job_id)
        if not job_info_str:
            error = f"Job info not found for job_id: {job_id}"
            logger.error(f"{error=}")
            result = _process_files_create_error_result(error, 400, job_id, data.get('parent_batch_id'), data.get('batch_upload_mode', False))
            publish('electronic_pdf_response', 'to_pipeline', result)
            return
        
        job_info = json.loads(job_info_str)
        
        # Extract required fields from job_info
        file_paths = job_info.get("file_paths", [])
        batch_id = job_info.get("batch_id")
        parent_batch_id = job_info.get("parent_batch_id")
        profile_name = job_info.get("profile_name")
        batch_upload_mode = job_info.get("batch_upload_mode", False)
        output_folder = job_info.get("output_folder")
        project = job_info.get("project")
        doc_type = job_info.get("doc_type", "")
        dpi = job_info.get("dpi", 300)
        
        if not file_paths:
            error = "file_paths not found."
            logger.error(f"{error=}")
            result = _process_files_create_error_result(error, 400, job_id, parent_batch_id, batch_upload_mode)
            publish('electronic_pdf_response', 'to_pipeline', result)
            return
        
        if not output_folder:
            error = "output_folder not found."
            logger.error(f"{error=}")
            result = _process_files_create_error_result(error, 400, job_id, parent_batch_id, batch_upload_mode)
            publish('electronic_pdf_response', 'to_pipeline', result)
            return
        
        if not batch_id:
            error = "batch_id not found."
            logger.error(f"{error=}")
            result = _process_files_create_error_result(error, 400, job_id, parent_batch_id, batch_upload_mode)
            publish('electronic_pdf_response', 'to_pipeline', result)
            return
        
        if not profile_name:
            error = "profile_name not found."
            logger.error(f"{error=}")
            result = _process_files_create_error_result(error, 400, job_id, parent_batch_id, batch_upload_mode)
            publish('electronic_pdf_response', 'to_pipeline', result)
            return
        
        if not project:
            error = "project not found."
            logger.error(f"{error=}")
            result = _process_files_create_error_result(error, 400, job_id, parent_batch_id, batch_upload_mode)
            publish('electronic_pdf_response', 'to_pipeline', result)
            return
        
        # Validate file paths exist
        for file_path in file_paths:
            if not Path(file_path).exists():
                error = f"File not found: {file_path}"
                logger.error(f"{error=}")
                result = _process_files_create_error_result(error, 400, job_id, parent_batch_id, batch_upload_mode)
                publish('electronic_pdf_response', 'to_pipeline', result)
                return
        
        # Process the files
        ra_json = process_files(
            file_paths=file_paths,
            output_folder=output_folder,
            batch_id=batch_id,
            profile_name=profile_name,
            project=project,
            doc_type=doc_type,
            dpi=dpi
        )
        
        # Update Redis with the processed data
        from utils.redis import set_redis_data
        set_redis_data(job_id, "ra_json", ra_json)
        
        response = {
            "status_code": 200,
            "parent_batch_id": parent_batch_id,
            "batch_upload_mode": batch_upload_mode,
            "job_id": job_id,
        }
        logger.info(f"Task completed: Processed {len(file_paths)} files for batch {batch_id}")
        
        # Always publish result to RabbitMQ
        publish('electronic_pdf_response', 'to_pipeline', response)
        
    except Exception as e:
        logger.error(f"Error in process_files_task: {e}")
        result = {"error": str(e), "status_code": 500, "job_id": data.get('job_id'), "parent_batch_id": data.get('parent_batch_id'), "batch_upload_mode": data.get('batch_upload_mode', False)}
        publish('electronic_pdf_response', 'to_pipeline', result)


def _process_files_create_error_result(error: str, status_code: int, job_id: str, parent_batch_id: str, batch_upload_mode: bool) -> Dict[str, Any]:
    """Create standardized error result dictionary for process_files_task."""
    return {
        "error": error,
        "status_code": status_code,
        "job_id": job_id,
        "parent_batch_id": parent_batch_id,
        "batch_upload_mode": batch_upload_mode
    }

print("Preprocess RabbitMQ handler loaded")
