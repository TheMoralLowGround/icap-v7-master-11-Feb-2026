import re
import base64
import requests
from datetime import timedelta
from django.utils import timezone

_session = requests.Session()


class OutputChannels:
    def __init__(self, channel):
        self.channel = channel

    def get_oauth2_token(self):
        """Fetch a new OAuth2 token if expired or missing"""
        if self.channel.token and self.channel.token_expires_at:
            if self.channel.token_expires_at > timezone.now():
                return self.channel.token

        if not (
            self.channel.token_url
            and self.channel.client_id
            and self.channel.client_secret
        ):
            raise ValueError("OAuth2 configuration missing")

        data={
            "grant_type": self.channel.grant_type,
            "client_id": self.channel.client_id,
            "client_secret": self.channel.client_secret,
        }

        if self.channel.grant_type == "password":
            data["grant_type"] = self.channel.grant_type
            data["username"] = self.channel.username
            data["password"] = self.channel.password

        if self.channel.scope:
            data["scope"] = self.channel.scope

        response = requests.post(
            self.channel.token_url,
            data=data,
        )
        response.raise_for_status()
        data = response.json()

        token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        try:
            self.channel.token = token
            self.channel.token_expires_at = timezone.now() + timedelta(
                seconds=expires_in
            )
            self.channel.save(update_fields=["_token", "token_expires_at"])
        except:
            pass
        return token

    def get_headers_and_auth(self):
        """Prepare headers or auth"""
        headers = {}
        if self.channel.auth_type == "basic":
            userpass = f"{self.channel.username}:{self.channel.password}"
            token = base64.b64encode(userpass.encode()).decode()
            headers["Authorization"] = f"Basic {token}"

        elif self.channel.auth_type == "token":
            headers["Authorization"] = f"Bearer {self.channel.token}"

        elif self.channel.auth_type == "api_key":
            headers[self.channel.api_key_name] = self.channel.api_key_value

        elif self.channel.auth_type == "oauth2":
            token = self.get_oauth2_token()
            headers["Authorization"] = f"Bearer {token}"

        return headers

    def dynamic_api_call(self, request_data, files=None, payload=None):
        """Function to make dynamic endpoint call"""
        try:
            request_type = self.channel.request_type
            endpoint_url = self.channel.endpoint_url

            for key, value in request_data.items():
                pattern = r"\{\{\s*" + re.escape(key) + r"\s*\}\}"
                endpoint_url = re.sub(pattern, str(value), endpoint_url)

            headers = self.get_headers_and_auth()
            request_kwargs = {
                "headers": headers,
                "timeout": 300,
            }

            if payload is not None:
                request_kwargs["json"] = payload

            if files is not None:
                request_kwargs["files"] = files

            response = _session.request(
                request_type,
                endpoint_url,
                **request_kwargs
            )
            return response

        except Exception as ex:
            print("RequestException:", str(ex))
            raise ex

    def get_timestamp_headers(self):
        """Prepare timestamp headers"""
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "IB_SL_RcptWebService_services_invokeWebService_Binder_IB_SL_RcptWebService",
        }
        if self.channel.auth_type == "api_key":
            headers[self.channel.api_key_name] = self.channel.api_key_value

        return headers

    def send_timestamp(self, form_data):
        """Function to send timestamp data"""
        try:
            request_type = self.channel.request_type
            endpoint_url = self.channel.endpoint_url
            headers = self.get_timestamp_headers()
            response = _session.request(
                request_type,
                endpoint_url,
                data=form_data,
                headers=headers,
                timeout=300,
            )
            return response

        except Exception as ex:
            print("RequestException:", str(ex))
            raise ex

    def send_json(self, final_json, shipment_id=None, case_id=None):
        """Main function to send final json"""
        try:
            request_type = self.channel.request_type
            endpoint_url = self.channel.endpoint_url
            if shipment_id:
                endpoint_url = f"{endpoint_url.rstrip('/')}/{shipment_id}"

            headers = self.get_headers_and_auth()
            if case_id:
                headers["case_id"] = case_id
            response = _session.request(
                request_type,
                endpoint_url,
                json=final_json,
                headers=headers,
                timeout=300,
            )
            return response

        except Exception as ex:
            print("RequestException:", str(ex))
            raise ex

    def send_document(self, form_data, files, case_id=None):
        """Main function to send document"""
        try:
            headers = self.get_headers_and_auth()
            if case_id:
                headers["case_id"] = case_id
            response = _session.request(
                self.channel.request_type,
                self.channel.endpoint_url,
                data=form_data,
                headers=headers,
                files=files,
                timeout=300,
            )
            return response

        except Exception as ex:
            print("RequestException:", str(ex))
            raise ex
