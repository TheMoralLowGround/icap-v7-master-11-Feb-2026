"""
Post-Processing Module
======================

Overview:
---------
This module performs post-processing tasks for a given job request. It retrieves 
the input data from Redis, assigns unique IDs to the elements in the JSON data, 
and updates the Redis database. Finally, it publishes the processing result to 
a RabbitMQ queue.

Key Components:
---------------
1. **Functions**:
   - `post_processing`: Main function to process the request data.
     - Retrieves the job request data from Redis using the job ID.
     - Checks for the presence of `data_json` in the request.
     - Assigns unique IDs to elements in the `data_json` using `assign_unique_id`.
     - Stores the processed `data_json` back in Redis.
     - Publishes the result (success or failure) to a RabbitMQ queue.

2. **External Dependencies**:
   - `get_redis_data`: Fetches job-related data from Redis using the job ID.
   - `set_redis_data`: Updates the job-related data in Redis.
   - `assign_unique_id`: Assigns unique IDs to elements in the JSON data.
   - `publish`: Publishes messages to a RabbitMQ queue.

Execution Flow:
---------------
1. Extract the `job_id` from the request data.
2. Fetch the request data associated with the job ID from Redis.
3. Validate that `data_json` exists in the retrieved request data.
4. Assign unique IDs to elements in the `data_json`.
5. Update the Redis store with the processed `data_json`.
6. Prepare the success response with:
   - `messages`: Any informational messages.
   - `job_id`: The job ID being processed.
   - `status_code`: Status code of the operation (200 for success).
7. Publish the success response to the RabbitMQ queue.
8. If an error occurs, prepare and publish an error response with:
   - `job_id`: The job ID being processed.
   - `error`: Error message.
   - `traceback`: Detailed traceback for debugging.
   - `status_code`: 400 to indicate failure.

Input Example:
--------------
```json
{
    "job_id": "job12345"
}
"""
import traceback

from rabbitmq_publisher import publish
from redis_utils import get_redis_data, set_redis_data

from app.misc_modules.unique_id import assign_unique_id


def post_processing(request_data):
    try:
        print("Processing Request")
        job_id = request_data["job_id"]
        request_data = get_redis_data(job_id)

        if not request_data.get("data_json"):
            return request_data

        d_json = request_data.get("data_json")

        # Assign unique IDs to each element in data json
        d_json = assign_unique_id(d_json)

        data_json = d_json
        set_redis_data(job_id, "data_json", data_json)

        result = {
            "messages": [],
            "job_id": job_id,
            "status_code": 200,
        }

        publish("post_processing_response", "to_pipeline", result)

    except Exception as error:
        result = {
            "job_id": job_id,
            "error": str(error),
            "traceback": traceback.print_exc(),
            "status_code": 400,
        }
        publish("post_processing_response", "to_pipeline", result)
