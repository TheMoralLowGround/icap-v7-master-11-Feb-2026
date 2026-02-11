import os
from .graph import GraphClient

GRAPH_BASE_URL = os.getenv("GRAPH_BASE_URL", "")


class CommonService(GraphClient):
    def list_sites(self):
        """List SharePoint sites"""
        url = f"{GRAPH_BASE_URL}/sites"
        response = self._request("GET", url)
        data = response.json()

        sites = [item for item in data.get("value", [])]
        return sites

    def list_site_drives(self, site_id):
        """List document libraries in a SharePoint site"""
        url = f"{GRAPH_BASE_URL}/sites/{site_id}/drives"
        response = self._request("GET", url)
        data = response.json()

        site_drives = [item for item in data.get("value", [])]
        return site_drives

    def list_drive_folder(self, drive_id, item_id):
        """List only folders inside a folder"""
        url = f"{GRAPH_BASE_URL}/drives/{drive_id}/items/{item_id}/children"
        response = self._request("GET", url)
        data = response.json()

        folders = [item for item in data.get("value", []) if "folder" in item]
        return folders

    def get_permissions(self, client_id):
        """Check API permissions"""
        sp_url = f"{GRAPH_BASE_URL}/servicePrincipals?$filter=appId eq '{client_id}'"
        response = self._request("GET", sp_url)
        sp = response.json()["value"][0]
        sp_id = sp["id"]

        permission_url = f"{GRAPH_BASE_URL}/servicePrincipals/{sp_id}/appRoleAssignments"
        response = self._request("GET", permission_url)
        data= response.json()

        permissions = [item["appRoleId"] for item in data.get("value", [])]
        return permissions


    def get_drive_id(self, user_id):
        """List users"""
        url = f"{GRAPH_BASE_URL}/users/{user_id}/drive"
        response = self._request("GET", url)
        data = response.json()
        drive_id = data["id"]
        return drive_id

    def get_user_sites(self, user_id):
        groups_url = f"{GRAPH_BASE_URL}/users/{user_id}/memberOf"
        groups_resp = self._request("GET", groups_url)
        groups = groups_resp.json().get("value", [])

        user_sites = []
        for g in groups:
            if g.get("groupTypes"):
                site_url = f"{GRAPH_BASE_URL}/groups/{g['id']}/sites/root"
                site_resp = self._request("GET", site_url)
                if site_resp.ok:
                    user_sites.append(site_resp.json())

        return user_sites