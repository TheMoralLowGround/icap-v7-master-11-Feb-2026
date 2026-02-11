import logging
from typing import Dict, Any
from producer import publish
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.views import process_title_classification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_title_classification_task(data: Dict[str, Any], message_type: str):
    """
    RabbitMQ task for title classification.
    
    Args:
        data (Dict[str, Any]): Dictionary containing classification parameters
            - layout_xml_paths: List of paths to RA JSON files
            - page_directions: Dict containing system_prompt, user_prompt, category
            - transaction_id: Batch identifier for logging
            - job_id: Job identifier for logging
    """
    transaction_id = data.get("transaction_id", "unknown")
    job_id = data.get("job_id", "unknown")
    
    logger.info(f"Starting title classification for transaction {transaction_id}")
    
    try:
        # Call the core classification function
        result = process_title_classification(data)
        result["job_id"] = job_id
        
        if "error" in result:
            result["status_code"] = 500
            logger.error(f"Title classification failed for transaction {transaction_id}: {result['error']}")
        else:
            result["status_code"] = 200
            logger.info(f"Title classification completed for transaction {transaction_id}")

        publish(f'{message_type}_response', 'to_pipeline', result)
    except Exception as error:
        # Handle unexpected errors
        logger.error(f"Unexpected error in title classification for transaction {transaction_id}: {error}")
        error_result = {
            "job_id": job_id,
            "status_code": 500,
            "error": f"Process failed: {str(error)}",
        }
        publish(f'{message_type}_response', 'to_pipeline', error_result)
