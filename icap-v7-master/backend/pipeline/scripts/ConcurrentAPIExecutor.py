"""
Organization: AIDocbuilder Inc.
File: scripts/ConcurrentAPIExecutor.py
Version: 6.0

Authors:
    - Nayem - Initial implementation

Last Updated By: Nayem
Last Updated At: 2024-12-11

Description:
    This script helps to handle parallel execution of multiple API calls using thread pooling.

Dependencies:
    - time, traceback
    - ThreadPoolExecutor, as_completed from concurrent.futures
    - List, Dict, Any, Tuple, Union, Callable from typing
    - get_customs_access_token from utils.assembly_api_utils

Main Features:
    - Execute multiple API calls in parallel.
    - Print execution summary statistics.
    - Handle EDM upload specific processing.
    - Handle API call errors.
"""

import time
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Union, Callable
from utils.assembly_api_utils import get_customs_access_token


class ConcurrentAPIExecutor:
    """
    A class to handle parallel execution of multiple API calls using thread pooling.
    """

    TIMESTAMP_API_INTERVAL = 0.0333  # 30 requests per second max

    def __init__(self, max_workers: int = 30, timeout: int = 300):
        """
        Initialize the ConcurrentAPIExecutor.

        Args:
            max_workers (int): Maximum number of concurrent threads (default: 30)
            timeout (int): Maximum time in seconds to wait for all calls (default: 300)
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.successful_calls_count = 0
        self.failed_calls_count = 0
        self._last_timestamp_call = 0
        self._timestamp_lock = threading.Lock()

    def _process_edm_upload(self, params: Dict[str, Any]) -> Tuple[Any, int, int]:
        """Handle EDM upload specific processing."""
        return (
            params["request_data"],
            params["status_code"],
            params["index"],
            params.get("parent_index"),
        )

    def _process_existing_response(
        self, params: Dict[str, Any]
    ) -> Tuple[Any, int, int]:
        """Handle cases where response already exists."""
        return (
            params["response_json"],
            params["status_code"],
            params["index"],
            params.get("parent_index"),
        )

    def _prepare_request_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare request data based on API type.

        Args:
            params (Dict[str, Any]): Contain parameters for the API call.

        Returns:
            request_data (Dict[str, Any]): The prepared request data for specific API type.

        Process Details:
            - Extract the 'request_data' from the 'params' dictionary.
            - Check the name of the callable API to determine the logic.

        Notes:
            - For the API 'get_shipment_status', return the 'response_json' from 'params' directly.
            - For the API 'upload_document_to_edm', if 'doc_number' exists then replace it with 'document_type'.
            - For the API 'upload_fcm_document_to_edm', if 'doc_number' exists then replace it with 'document_type'.
        """
        request_data = params["request_data"]

        if params["callable_api"].__name__ == "get_shipment_status":
            return params["response_json"]

        if params["callable_api"].__name__ in [
            "upload_document_to_edm",
            "upload_fcm_document_to_edm",
        ]:
            if "doc_number" in request_data:
                request_data["document_type"] = request_data.pop("doc_number")

            if "doc_code" in request_data:
                request_data["document_type"] = request_data.pop("doc_code")

        return request_data

    def _submit_api_call(
        self, executor: ThreadPoolExecutor, params: Dict[str, Any], token: str = None
    ) -> Tuple[Any, int]:
        """
        Submit API call to thread executor based on API type.

        Args:
            executor (ThreadPoolExecutor): Managing concurrent API calls.
            params (Dict[str, Any]): Contain parameters for the API call.
            token (str): Authentication token.

        Returns:
            Tuple[Any, int]: Representing the submitted API call.

        Raise:
            ValueError: if the API type is unsupported.

        Process Details:
            - Prepare the request data by calling '_prepare_request_data()'.
            - Identify the API type by 'params["callable_api"].__name__'.

        Notes:
            - For 'upload_document_to_edm', submit the API call with unpacked 'request_data'.
            - For 'upload_fcm_document_to_edm', submit the API call with unpacked 'request_data'.
            - For 'get_shipment_status', submit the API call with 'request_data' as an argument.
            - For 'send_shipment_create_json', submit the API call with 'request_data' and 'token'.
        """
        request_data = self._prepare_request_data(params)
        api_name = params["callable_api"].__name__

        if api_name in ["upload_document_to_edm", "upload_fcm_document_to_edm"]:
            return executor.submit(params["callable_api"], **request_data)
        elif api_name == "get_shipment_status":
            return executor.submit(params["callable_api"], request_data)
        elif api_name == "send_shipment_create_json":
            return executor.submit(params["callable_api"], request_data, token)
        elif api_name == "send_shipment_time_stamp":
            # Apply throttling for timestamp API
            with self._timestamp_lock:
                current_time = time.time()
                elapsed = current_time - self._last_timestamp_call

                if (
                    elapsed < self.TIMESTAMP_API_INTERVAL
                    and self._last_timestamp_call > 0
                ):
                    sleep_time = self.TIMESTAMP_API_INTERVAL - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                # Update last call time
                self._last_timestamp_call = time.time()

            return executor.submit(params["callable_api"], **request_data)

        raise ValueError(f"Unsupported API type: {api_name}")

    def _handle_api_error(
        self, e: Exception, params: Dict[str, Any]
    ) -> Union[int, Tuple[Dict[str, str], int]]:
        """
        Handle API call errors.

        Args:
            e (Exception): Exception object raised during the API call.
            params (Dict[str, Any]): Contain parameters for the API call.

        Returns:
            Union[int, Tuple[Dict[str, str], int]]

        Process Details:
            - Capture the traceback of the exception and print it for debugging.
            - Identify the API type.

        Notes:
            - For 'upload_document_to_edm', return status code of 400.
            - For 'upload_fcm_document_to_edm', return status code of 400.
            - For other API types, returns an error dictionary with a code and message, along with status code of 400.
        """
        trace = traceback.format_exc()
        print(f"{trace=}")

        if params["callable_api"].__name__ in [
            "upload_document_to_edm",
            "upload_fcm_document_to_edm",
        ]:
            return 400

        return {
            "code": "AIDB-108",
            "message": f"AIDB-108: The following error occurred - ''{str(e)}'' ",
        }, 400

    def execute(self, final_jsons: List[Dict[str, Any]]) -> List[Tuple[Any, int, int]]:
        """
        Execute multiple API calls in parallel and handle their results.

        Args:
            final_jsons: List of parameter dictionaries for each API call

        Returns:
            List of tuples containing (response_data, status_code, index)

        Raises:
            TimeoutError: If execution exceeds the timeout period
            Exception: If any API call fails

        Process Details:
            - Retrieve an access token using 'get_customs_access_token'.
            - Use 'ThreadPoolExecutor' to submit and process API calls concurrently.
            - Skip empty entries with a placeholder result in 'final_jsons'.
            - Process EDM upload calls directly with '_process_edm_upload'.
            - If response with a 'status_code' of 200 is found, process it using '_process_existing_response'.
            - Otherwise, submit the API call using '_submit_api_call' and store its 'future' with the index.
            - Update the results list with the processed response and index.
            - Print execution summary, including timing and call counts.

        Notes:
            - Timeout for completing all 'future' is specified by 'self.timeout'.
            - For success api call, increment the successful calls count.
            - For error, handle the exception with '_handle_api_error' and increment the failed calls count.
        """
        results = [({}, None, None, None)] * len(final_jsons)
        self.successful_calls_count = 0
        self.failed_calls_count = 0
        start_time = time.time()

        token = get_customs_access_token()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {}

            # Submit API calls
            for index, params in enumerate(final_jsons):
                # Skip the API call if the params is empty or invalid
                invalid_params = (
                    not params or not isinstance(params, dict) or len(params) == 2
                )
                if invalid_params:
                    parent_index = (
                        params.get("parent_index") if isinstance(params, dict) else None
                    )
                    results[index] = ({}, None, index, parent_index)
                    continue

                params["index"] = index

                # Handle EDM upload specific processing.
                if params["callable_api"].__name__ in [
                    "upload_document_to_edm",
                    "upload_fcm_document_to_edm",
                ]:
                    results[index] = self._process_edm_upload(params)

                # Skip the API call if the status_code is 200
                if params.get("status_code") == 200:
                    results[index] = self._process_existing_response(params)
                    continue

                future = self._submit_api_call(executor, params, token)
                future_to_index[future] = {
                    "index": index,
                    "parent_index": params.get("parent_index"),
                }

            # Process completed calls
            for future in as_completed(future_to_index, timeout=self.timeout):
                try:
                    result = future.result()
                    self.successful_calls_count += 1
                except Exception as e:
                    self.failed_calls_count += 1
                    result = self._handle_api_error(e, params)

                index, parent_index = future_to_index[future].values()
                if isinstance(result, tuple):
                    results[index] = (*result, index, parent_index)
                else:
                    results[index] = (results[index][0], result, index, parent_index)

        self._print_execution_summary(start_time, len(future_to_index))
        return results

    def _print_execution_summary(self, start_time: float, total_calls: int):
        """Print execution summary statistics."""
        execution_time = time.time() - start_time
        success_rate = (
            (self.successful_calls_count / total_calls) * 100 if total_calls > 0 else 0
        )

        print(f"\nExecution complete:")
        print(f"Total time: {execution_time:.2f} seconds")
        print(
            f"Successful calls: {self.successful_calls_count}/{total_calls} ({success_rate:.1f}%)"
        )
        print(f"Failed calls: {self.failed_calls_count}")
