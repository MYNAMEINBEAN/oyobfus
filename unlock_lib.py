# unlock_lib.py  (installable as a pip package for your users)
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LICENSE_SERVER = os.environ.get("LICENSE_SERVER_URL", "https://your-license-server.example")  # set this env
# For this demo, the client will send a 'license_token' header or body value. In practice the user obtains it from your web UI.
def _session():
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5)
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

def get_symkey_for_license(license_id: str, license_token: str = None) -> str:
    """
    Returns base64-encoded symmetric key as a string, or raises on error.
    The loader will call this function without license_token; for demo we read it from env var.
    """
    token = license_token or os.environ.get("USER_LICENSE_TOKEN")
    if not token:
        raise RuntimeError("No license token provided. Set USER_LICENSE_TOKEN env or pass token explicitly")

    url = LICENSE_SERVER.rstrip("/") + "/get_key"
    s = _session()
    resp = s.post(url, json={"license_id": license_id, "license_token": token}, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"license server error: {resp.status_code} {resp.text}")
    data = resp.json()
    return data["key_b64"]
