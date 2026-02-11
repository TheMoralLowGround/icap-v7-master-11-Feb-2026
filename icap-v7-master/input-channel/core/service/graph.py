import os
import msal
import time
import requests

MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
GRAPH_TIMEOUT = int(os.getenv("GRAPH_TIMEOUT", 30))

_session = requests.Session()

class GraphClient:
    def __init__(self, client_id, client_secret, tenant_id=None):
        if not (client_id and client_secret):
            raise RuntimeError("Missing Azure app credentials")

        self._client_id = client_id
        self._client_secret = client_secret
        self._tenant_id = tenant_id

        if self._tenant_id:
            self._authority = f"https://login.microsoftonline.com/{self._tenant_id}"
        else:
            self._authority = "https://login.microsoftonline.com/common"

        self._token_cache = msal.SerializableTokenCache()
        self._cca = msal.ConfidentialClientApplication(
            client_id=self._client_id,
            client_credential=self._client_secret,
            authority=self._authority,
            token_cache=self._token_cache
        )

    def _get_token(self, scopes=None):
        # Try silent first
        if scopes is None:
            scopes = ["https://graph.microsoft.com/.default"]
        result = self._cca.acquire_token_silent(scopes, account=None)
        if not result:
            result = self._cca.acquire_token_for_client(scopes=scopes)
        if "access_token" not in result:
            raise RuntimeError(result)

        return result["access_token"]

    def _request(self, method, url, **kwargs):
        token = self._get_token()
        headers = kwargs.pop("headers", {})
        headers.setdefault("Authorization", f"Bearer {token}")
        headers.setdefault("Accept", "application/json")

        backoff = 1
        for attempt in range(1, MAX_RETRIES + 1):
            response = _session.request(method, url, headers=headers, timeout=GRAPH_TIMEOUT, **kwargs)

            if response.status_code in (429, 503, 504):
                retry_after = response.headers.get("Retry-After")
                sleep_for = int(retry_after) if retry_after and retry_after.isdigit() else backoff
                time.sleep(sleep_for)
                backoff = min(backoff * 2, 30)
                continue

            if 200 <= response.status_code < 300:
                return response

            try:
                body = response.json()
            except Exception:
                body = response.text
            print("Graph request failed (%s): %s", response.status_code, body)

        return response

    def to_dict(self):
        return {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "tenant_id": self._tenant_id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
