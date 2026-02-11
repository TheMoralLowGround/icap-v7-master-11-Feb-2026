import json
from core.models import PostProcess
from rabbitmq.producer import publish


def _send_error_response(batch_id, error_message, response_queue):
    """Send error response with consistent format"""
    publish(
        "postprocess_output_json_response",
        response_queue,
        {"batch_id": batch_id, "status_code": 400, "error": error_message},
    )


def _send_success_response(batch_id, process_name, final_output_jsons, response_queue):
    """Send success response with transformed data"""
    publish(
        "postprocess_output_json_response",
        response_queue,
        {
            "status_code": 200,
            "process_name": process_name,
            "final_output_jsons": final_output_jsons,
            "batch_id": batch_id,
        },
    )


def _validate_payload(payload):
    """Validate required fields in payload"""
    batch_id = payload.get("batch_id")
    process_name = payload.get("process_name") or payload.get("process")
    final_output_jsons = payload.get("final_output_jsons")
    
    if not process_name:
        return None, None, None, "Missing required field: process_name"
    
    if final_output_jsons is None:
        return None, None, None, "Missing required field: final_output_jsons"
    
    return batch_id, process_name, final_output_jsons, None


def _get_postprocess_code(process_name):
    """Get the latest postprocess code for the given process name"""
    postprocess = (
        PostProcess.objects.filter(process=process_name)
        .order_by("-created_at")
        .first()
    )
    
    if not postprocess or not postprocess.code:
        return None, f"PostProcess not found for '{process_name}'"
    
    return postprocess.code, None


def _execute_transform_code(code):
    """Execute the transform code and return the transform function"""
    try:
        exec_namespace = {}
        exec(code, exec_namespace)
        transform_func = exec_namespace.get('transform_json')
        
        if not transform_func:
            return None, "transform_json function not found in code"
        
        return transform_func, None
    except Exception as e:
        return None, f"Code execution error: {str(e)}"


def _transform_data_items(transform_func, final_output_jsons):
    """Transform each item in the final_output_jsons array"""
    updated_output_jsons = []
    
    for item in final_output_jsons:
        if isinstance(item, dict):
            try:
                transformed_item = transform_func(item)
                updated_output_jsons.append(transformed_item)
            except Exception as e:
                raise Exception(f"Transform error on item: {str(e)}")
        else:
            # Keep non-dict items as-is
            updated_output_jsons.append(item)
    
    return updated_output_jsons


def handle_transform_message(body, response_queue="to_pipeline"):
    """
    Handle postprocess transformation requests.
    
    Args:
        body: JSON string containing the transformation request
        response_queue: Queue name for sending responses
    """
    try:
        # Parse and validate payload
        payload = json.loads(body)
        batch_id, process_name, final_output_jsons, error = _validate_payload(payload)
        
        if error:
            _send_error_response(batch_id, error, response_queue)
            return
        
        # Get postprocess code
        code, error = _get_postprocess_code(process_name)
        if error:
            _send_error_response(batch_id, error, response_queue)
            return
        
        # Execute transform code
        transform_func, error = _execute_transform_code(code)
        if error:
            _send_error_response(batch_id, error, response_queue)
            return
        
        # Transform data
        try:
            updated_output_jsons = _transform_data_items(transform_func, final_output_jsons)
        except Exception as e:
            _send_error_response(batch_id, str(e), response_queue)
            return
        
        # Send success response
        _send_success_response(batch_id, process_name, updated_output_jsons, response_queue)
        
    except json.JSONDecodeError:
        _send_error_response(None, "Invalid JSON format", response_queue)
    except Exception as e:
        _send_error_response(
            payload.get("batch_id") if 'payload' in locals() else None,
            f"Unexpected error: {str(e)}",
            response_queue
        )
