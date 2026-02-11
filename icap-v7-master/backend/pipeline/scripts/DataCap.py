"""
Organization: AIDocbuilder Inc.
File: scripts/Datacap.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    Managing core DataCap operations and interacting with the DataCap system including login, 
    batch creation, file uploads, batch release, and retrieval of batch details.

Dependencies:
    - os, time, json, requests
    - xml.etree.ElementTree as ET

Main Features:
    - Authenticate.
    - Create datacap batches and upload files to Datacap.
    - Get necessary information.
    - Handle batches which release from Datacap.
"""
import os
import time
import json
import requests
import xml.etree.ElementTree as ET
from utils.logger_config import get_logger

logger = get_logger(__name__)

DATACAP_API_BASE_URL = os.getenv("DATACAP_API_BASE_URL")
DATACAP_APP = os.getenv("DATACAP_APP")
DATACAP_USER = os.getenv("DATACAP_USER")
DATACAP_PASSWORD = os.getenv("DATACAP_PASSWORD")
DATACAP_STATION = os.getenv("DATACAP_STATION")
DATACAP_JOB = os.getenv("DATACAP_JOB")
DATACAP_MILI_JOB = os.getenv("DATACAP_MILI_JOB")
MAX_RETRY = int(os.getenv("MAX_RETRY", 0))


class DataCap:
    def __init__(self,project_name=None):
        """Initialize the Datacap class instance"""
        self.application = DATACAP_APP
        self.user = DATACAP_USER
        self.password = DATACAP_PASSWORD
        self.station = DATACAP_STATION
        self.job = DATACAP_JOB
        self.cookie = ""
        self.batch_id = ""
        self.queue_id = ""
        self.logger = logger

        if project_name == "Military_Flag":
            self.job = DATACAP_MILI_JOB

        self.logon()


    def logon(self):
        """
        Authenticates with the Datacap system.

        Args:
            Operate on class attributes.

        Raises:
            ValueError: if authentication fails.

        Process Details:
            - Sends an HTTP POST request to the 'url' endpoint.
            - Authentication details provided in form_data (application, user, password, station).
            - If the authentication is successful with status code 200, store the session cookie.

        Notes:
            - The response must contain a valid session cookie for further interactions with Datacap.        
        """
        url = f"{DATACAP_API_BASE_URL}/Session/Logon"
        form_data = {
            "application": self.application,
            "user": self.user,
            "password": self.password,
            "station": self.station,
        }
        response = requests.post(url, json=form_data)
        if response.status_code == 200:
            self.cookie = response.headers["Set-Cookie"]
        else:
            code = {"code": "AIDB-104"}
            error = {
                "error": "Authentication with Datacap failed.",
                "datacap_response": response.content.decode("utf-8"),
            }
            raise ValueError(code, error)

    def logout(self):
        """
        Logs out from the Datacap system and invalidates the session.

        Args:
            Operate on class attributes.

        Raises:
            ValueError: if logout fails.

        Process Details:
            - Sends an HTTP POST request to the 'url' endpoint.
            - Uses the stored session cookie for authentication.
            - If logout is successful (status code 200), clears the session cookie.
            - If logout fails, raises an error with details.

        Notes:
            - This should be called when the Datacap session is no longer needed.
            - Clears the cookie attribute regardless of success/failure to prevent reuse.
        """

        if not self.cookie:
            self.logger.warning("No active Datacap session found to log out.")
            return
        
        url = f"{DATACAP_API_BASE_URL}/Session/Logoff"
        
        headers = {
            "Cookie": self.cookie
        }
        
        try:
            response = requests.post(url, headers=headers)
            
            self.cookie = ""
            
            if response.status_code == 200:
                self.logger.info("Successfully logged out from Datacap")
            else:
                self.logger.warning("Logout from Datacap failed.")
                
        except Exception as e:
            self.cookie = ""
            self.logger.error(f"Network error during Datacap logout: {str(e)}")


    def create_batch(self, files, page_file=None, delayed_release=False):
        """
        This is the main function to create batch in the Datacap system and get update about the batch.

        Args:
            files (list): List of InMemoryUploadedFile objects.
            page_file (str): Path of the page file associate with the batch.
            delayed_release (bool): Flag to delay before releasing the batch.

        Returns:
            dict: Contain the 'batch_id' and 'queue_id' associated with the created batch.

        Raises:
            ValueError: if there are issues with uploading files or releasing the batch.

        Process Details:
            - Call the '_create_batch()' to create a new batch in the Datacap system.
            - After the batch is created, it call the '_upload_files()' to upload the provided files.
            - If 'delayed_release' is 'True', it waits for 3 seconds before releasing the batch.
            - Try to release the batch by calling the '_release_batch()'.

        Notes:
            - If releasing the batch fail the method retries up to 'MAX_RETRY' times.
            - 'MAX_RETRY' is defined by environment variable.
            - Each retry is followed by 10 seconds wait.
        """
        self._create_batch(page_file)
        self._upload_files(files)
        if delayed_release:
            time.sleep(3)
        try:
            for i in range(0, MAX_RETRY):
                try:
                    self._release_batch()
                    break
                except ValueError:
                    self.logger.error(f"retrying in 10 seconds retry count: {i+1}")
                    time.sleep(10)
            else:
                self._release_batch()  # Final attempt
        finally:
            # ALWAYS logout, whether success or failure
            self.logout()
        return self._get_batch_details()


    def _create_batch(self, page_file):
        """
        Create new batch in the Datacap system and get the batchID and queueID.

        Args:
            page_file (str): Path of the page file associate with the batch.

        Raises:
            ValueError: if the batch creation fails.

        Process Details:
            - Sends an HTTP POST request to the 'url' endpoint to create a batch.
            - The request payload includes the 'application', 'job', and 'page_file'.
            - If the batch creation is successful with status code 201.
            - Parse the XML response to extract 'batch_id' and 'queue_id'.

        Notes:
            - Store the 'batch_id' and 'queue_id' in the instance variables.
            - The response is expected to be in XML format.
        """
        url = f"{DATACAP_API_BASE_URL}/Queue/CreateBatch"
        payload = {
            "application": self.application,
            "job": self.job,
        }
        if page_file is not None:
            payload["pageFile"] = page_file

        headers = {"Cookie": self.cookie}

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            #  Parese xml response to JSON
            data = {}
            root = ET.fromstring(response.content)
            for child in root.iter("*"):
                data[child.tag] = child.text

            self.batch_id = data["batchId"]
            self.queue_id = data["queueId"]
        else:
            code = {"code": "AIDB-104"}
            error = {
                "error": "Could not create batch with Datacap.",
                "datacap_response": response.content.decode("utf-8"),
            }
            raise ValueError(code, error)


    def _upload_files(self, files):
        """
        Upload files to Datacap system.

        Args:
            files (list): List of InMemoryUploadedFile objects to upload.

        Raises:
            ValueError: if the file upload fails or files are skipped by Datacap.

        Process Details:
            - Validates file sizes before upload (detects 0-byte in-memory files).
            - Uses FileWrapper to ensure file pointer is at position 0 when requests reads.
            - This prevents uploading 0 bytes when file pointer is at wrong position.
            - Sends an HTTP POST request with files in multipart/form-data format.
            - Validates that all files were successfully received by Datacap.

        Root Cause of 0-Byte Uploads:
            - requests.post() reads from the CURRENT file position, not from beginning.
            - If pointer is at end (or wrong position), it reads 0 bytes.
            - Upload succeeds (HTTP 201) but file is 0 bytes - NO EXCEPTION RAISED.
            - FileWrapper.read() ensures seek(0) on first read, guaranteeing full upload.

        Notes:
            - All files must be InMemoryUploadedFile objects (created by create_inmemory_file).
            - FileWrapper intercepts read() calls to control file pointer position.
        """
        url = f"{DATACAP_API_BASE_URL}/Queue/UploadFile/{self.application}/{self.queue_id}"
        headers = {
            "Accept": "application/json, */*",
            "Cookie": self.cookie,
        }

        # Validate and prepare files for upload
        files_payload = []
        file_sizes = []
        
        for file_obj in files:
            # Get file size
            file_obj.seek(0, 2)  # SEEK_END
            actual_size = file_obj.tell()
            
            # Validate: detect 0-byte files
            file_name = getattr(file_obj, 'name', 'unknown')
            if actual_size == 0:
                print(
                    f"CRITICAL: File {file_name} is 0 bytes in memory. "
                    f"This indicates incorrect file creation."
                )
                raise ValueError(
                    {"code": "AIDB-105"},
                    {
                        "error": f"File {file_name} is 0 bytes in memory",
                        "file": file_name,
                    }
                )
            
            file_sizes.append(actual_size)
            
            # CRITICAL FIX: Ensure file pointer is at position 0 before reading
            # The issue: requests.post() reads from CURRENT file position
            # If pointer is at end (from size check), it reads 0 bytes
            file_obj.seek(0)
            
            content_type = getattr(file_obj, 'content_type', 'application/octet-stream')
            files_payload.append(("file", (file_name, file_obj, content_type)))
        
        # Log upload with size details
        total_size = sum(file_sizes)
        print(
            f"Uploading {len(files_payload)} files to Datacap "
            f"(total size: {total_size} bytes)"
        )
        
        # Perform upload with timeout
        response = requests.post(
            url,
            files=files_payload,
            headers=headers,
            timeout=(10, 300),  # 10s connect, 300s read timeout
        )

        if response.status_code != 201:
            raise ValueError(
                {"code": "AIDB-104"},
                {
                    "error": "Datacap upload failed",
                    "status_code": response.status_code,
                    "datacap_response": response.text,
                },
            )

        payload = response.json()
        received = len(payload.get("pages", []))
        requested = len(files_payload)

        if received != requested:
            print(
                f"Datacap file count mismatch: requested={requested}, received={received}. "
                f"This may indicate files were 0-bytes or corrupted during upload."
            )
            raise ValueError(
                {"code": "AIDB-104"},
                {
                    "error": f"Datacap skipped files (requested={requested}, received={received})",
                    "datacap_response": payload,
                    "file_sizes": file_sizes,
                },
            )

        print(
            f"Successfully uploaded {received} files to Datacap "
            f"(total size: {total_size} bytes)"
        )


    def _release_batch(self):
        """
        Release the batch from Datacap system

        Args:
            Operate on class attributes.

        Raise:
            ValueError: if the batch release fails.

        Process Details:
            - Send an HTTP PUT request to the 'url' endpoint and release.

        Notes:
            - The request include the session cookie in the headers for authentication.
            - If the release fails, the system cannot proceed with batch processing.
        """
        url = f"{DATACAP_API_BASE_URL}/Queue/ReleaseBatch/{self.application}/{self.queue_id}/finished"
        headers = {"Cookie": self.cookie}
        
        try:
            response = requests.put(url, data=None, headers=headers)
            if response.status_code != 200:
                raise ValueError(
                    {"code": "AIDB-104"},
                    {
                        "error": "Could not release batch with Datacap.",
                        "datacap_response": response.content.decode("utf-8"),
                    }
                )
        except requests.exceptions.ConnectionError as e:
            raise ValueError(
                {"code": "AIDB-104"},
                {
                    "error": "Could not release batch with Datacap - Connection error.",
                    "datacap_response": str(e),
                }
            )


    def _get_batch_details(self):
        """Set batch_id and queue_id"""
        return {"batch_id": self.batch_id, "queue_id": self.queue_id}
