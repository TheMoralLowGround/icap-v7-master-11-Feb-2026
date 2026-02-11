import os
from .graph import GraphClient

GRAPH_BASE_URL = os.getenv("GRAPH_BASE_URL")

class OutlookService(GraphClient):
    def get_unread_emails(self, mailbox):
        """Get unread emails list"""
        filter_query = f"isRead eq false and from/emailAddress/address ne '{mailbox}'"
        url = f"{GRAPH_BASE_URL}/users/{mailbox}/messages?$filter={filter_query}&$top=100"
        response = self._request("GET", url)
        messages = response.json().get("value", [])
        return messages

    def fetch_email(self, mailbox, message_id):
        """Fetch eml message"""
        url = f"{GRAPH_BASE_URL}/users/{mailbox}/messages/{message_id}/$value"
        headers={"Accept": "message/rfc822"}
        response = self._request("GET", url, headers=headers)
        return response.content

    def mark_read(self, mailbox, message_id):
        """Mark the mail as read"""
        url = f"{GRAPH_BASE_URL}/users/{mailbox}/messages/{message_id}"
        body = {"isRead": True}
        headers = {"Content-Type": "application/json"}
        self._request(
            "PATCH",
            url,
            json=body,
            headers=headers
        )

    def move_to_archive(self, mailbox, message_id):
        """Move the mail to archive folder"""
        url = f"{GRAPH_BASE_URL}/users/{mailbox}/messages/{message_id}/move"
        body = {"destinationId": "archive"}
        headers = {"Content-Type": "application/json"}
        self._request(
            "POST",
            url,
            json=body,
            headers=headers
        )
