"""Client for the shared Google Workspace OAuth service."""
from __future__ import annotations

from hashlib import sha256
import json
import os
import re
import secrets
from urllib.parse import parse_qs, urlsplit

import requests

PUBLIC_ORIGIN = ""
PATH = "/v1/connections/gmail"
KEY = re.compile(r"[A-Za-z0-9_-]{43}\Z")


class ServiceError(Exception):
    def __init__(self, code):
        self.code = code


def origin() -> str:
    override = os.environ.get("GMAIL_WORKSPACE_OAUTH_URL")
    value = (override if override is not None else PUBLIC_ORIGIN).rstrip("/")
    if not value:
        return ""
    parsed = urlsplit(value)
    loopback = override and parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
    if (not parsed.hostname or parsed.username is not None or parsed.path or parsed.query
            or parsed.fragment or (parsed.scheme != "https" and not loopback)):
        raise ServiceError("service_configuration")
    return value


def request(base, method, path=PATH, *, proof=None, body=None):
    headers = {"Authorization": f"Bearer {proof}"} if proof else {}
    with requests.Session() as session:
        session.trust_env = False
        try:
            with session.request(method, base + path, headers=headers, json=body,
                                 timeout=(4, 8), allow_redirects=False, stream=True) as response:
                if response.status_code == 204 and method == "DELETE":
                    return {}
                data = bytearray()
                for chunk in response.iter_content(4096):
                    data.extend(chunk)
                    if len(data) > 16384:
                        raise ServiceError("invalid_service_response")
                result = json.loads(data)
                status = response.status_code
        except (requests.RequestException, ValueError):
            raise ServiceError("service_unavailable") from None
    if not isinstance(result, dict):
        raise ServiceError("invalid_service_response")
    if status not in (200, 201, 202):
        error = result.get("error")
        if error in ("reauth_required", "authorization_denied", "scope_or_grant_incomplete"):
            raise ServiceError(error)
        raise ServiceError("service_unavailable")
    return result


def start(base, allowed_scopes):
    proof = secrets.token_urlsafe(32)
    result = request(base, "POST", body={"key_hash": sha256(proof.encode()).hexdigest()})
    url = result.get("authorization_url")
    if not isinstance(url, str) or not 0 < len(url) <= 4096:
        raise ServiceError("invalid_service_response")
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    if (parsed.scheme != "https" or parsed.netloc != "accounts.google.com"
            or parsed.path != "/o/oauth2/v2/auth" or parsed.fragment
            or query.get("response_type") != ["code"] or query.get("code_challenge_method") != ["S256"]
            or len(query.get("state", [])) != 1 or len(query.get("scope", [])) != 1
            or set(query["scope"][0].split()) != set(allowed_scopes)):
        raise ServiceError("invalid_service_response")
    return proof, url


def token(base, proof):
    result = request(base, "POST", PATH + "/token", proof=proof)
    if result.get("status") == "pending":
        return None
    access = result.get("access_token")
    expires = result.get("expires_in")
    if (result.get("status") != "connected" or not isinstance(access, str) or not access
            or type(expires) is not int or not 0 < expires <= 86400
            or not isinstance(result.get("scopes"), list)):
        raise ServiceError("invalid_service_response")
    return result


def disconnect(base, proof):
    request(base, "DELETE", proof=proof)
