import os
from .graph import GraphClient

GRAPH_BASE_URL = os.getenv("GRAPH_BASE_URL")

class OneDriveService(GraphClient):
    def folder_details(self, encoded_url):
        """Get folder details from url"""
        url = f"{GRAPH_BASE_URL}/shares/u!{encoded_url}/driveItem"
        response = self._request("GET", url)
        return response.json()

    def list_files(self, user_email, folder_path, extensions=None):
        """List files in OneDrive folder"""
        url = f"{GRAPH_BASE_URL}/users/{user_email}/drive/root:/{folder_path}:/children"
        response = self._request("GET", url)
        files = response.json().get("value", [])

        if extensions:
            extensions = [ext.lower() for ext in extensions]
            files = [
                f for f in files
                if "file" in f  # ensure it's a file, not folder
                and any(f["name"].lower().endswith(ext) for ext in extensions)
            ]

        return files

    def download_file(self, user_email, file_id):
        """Download a file from OneDrive"""
        url = f"{GRAPH_BASE_URL}/users/{user_email}/drive/items/{file_id}/content"
        headers = {"Accept": "application/octet-stream"}
        response = self._request("GET", url, headers=headers)
        return response.content

    def move_file(self, user_email, file, archive_folder_path):
        """Move a file to archive folder"""
        archive_url = f"{GRAPH_BASE_URL}/users/{user_email}/drive/root:/{archive_folder_path}"
        folder_body = {"folder": {}, "@microsoft.graph.conflictBehavior": "replace"}
        self._request("PUT", archive_url, json=folder_body)

        archive_files = self.list_files(user_email=user_email, folder_path=archive_folder_path)
        archive_file_names = [file["name"].lower() for file in archive_files]

        file_id = file["id"]
        file_name = file["name"]
        name, ext = os.path.splitext(file_name)

        counter = 0
        while file_name.lower() in archive_file_names:
            file_name = f"{name}_{counter}{ext}"
            counter += 1
    
        move_url = f"{GRAPH_BASE_URL}/users/{user_email}/drive/items/{file_id}"
        body = {
            "parentReference": {"path": f"/drive/root:/{archive_folder_path}"},
            "name": file_name
        }
        headers = {"Content-Type": "application/json"}
        self._request(
            "PATCH",
            move_url,
            json=body,
            headers=headers
        )
