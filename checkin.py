import os
import time
import hashlib
import json
import base64
import requests
from Crypto.Cipher import AES
from datetime import datetime


class JMCheckIn:
    jm_version = "2.0.16"
    jm_pkg_name = "com.example.app"
    jm_auth_key = "18comicAPPContent"
    kjm_secret = "185Hcomic3PAPP7R"
    domain_url = "https://rup4a04-c02.tos-cn-hongkong.bytepluses.com/newsvr-2025.txt"
    domain_secret = "diosfjckwpqpdfjkvnqQjsik"

    fallback_servers = [
        "www.cdntwice.org",
        "www.cdnsha.org",
        "www.cdnaspa.cc",
        "www.cdnntr.cc",
    ]

    base_headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Origin": "https://localhost",
        "Referer": "https://localhost/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "X-Requested-With": jm_pkg_name,
    }

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = None
        self._get_domains()

    def _decrypt_data(self, input_data, secret):
        key = hashlib.md5(secret.encode()).hexdigest().encode("utf-8")
        data = base64.b64decode(input_data)
        cipher = AES.new(key, AES.MODE_ECB)
        decrypted = cipher.decrypt(data)
        text = decrypted.decode("utf-8", errors="ignore")
        start = 0
        while start < len(text) and text[start] not in ("{", "["):
            start += 1
        end = len(text) - 1
        while end > start and text[end] not in ("}", "]"):
            end -= 1
        return text[start:end + 1]

    def _get_domains(self):
        print("[*] Fetching domain list...")
        servers = []
        try:
            resp = requests.get(self.domain_url, headers=self.base_headers, timeout=10)
            if resp.status_code == 200:
                raw = resp.content.decode("utf-8-sig").strip()
                data = json.loads(self._decrypt_data(raw, self.domain_secret))
                servers = data.get("Server", [])[:4]
                print(f"[OK] Got {len(servers)} domains from API")
        except Exception as e:
            print(f"[WARN] API domain fetch failed: {e}")

        if not servers:
            servers = self.fallback_servers[:]
            print(f"[INFO] Using {len(servers)} fallback domains")

        self.servers = servers

    def _get_api_headers(self, timestamp):
        token_raw = hashlib.md5(f"{timestamp}{self.jm_auth_key}".encode()).digest()
        return {
            **self.base_headers,
            "Authorization": "Bearer",
            "Sec-Fetch-Storage-Access": "active",
            "token": token_raw.hex(),
            "tokenparam": f"{timestamp},{self.jm_version}",
        }

    def _decrypt_response(self, encrypted_b64, timestamp):
        secret = f"{timestamp}{self.kjm_secret}"
        key = hashlib.md5(secret.encode()).hexdigest().encode("utf-8")
        data = base64.b64decode(encrypted_b64)
        cipher = AES.new(key, AES.MODE_ECB)
        decrypted = cipher.decrypt(data)
        text = decrypted.decode("utf-8", errors="ignore")
        start = 0
        while start < len(text) and text[start] not in ("{", "["):
            start += 1
        end = len(text) - 1
        while end > start and text[end] not in ("}", "]"):
            end -= 1
        return text[start:end + 1]

    def _try_login(self, server):
        self.base_url = f"https://{server}"
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.0.0 Mobile Safari/537.36"
        })

        timestamp = int(time.time())
        headers = {
            **self._get_api_headers(timestamp),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            resp = session.post(
                f"{self.base_url}/login",
                headers=headers,
                data=f"username={self.username}&password={self.password}",
                timeout=15,
            )
            if resp.status_code != 200:
                return None
            body = resp.json()
            decrypted = self._decrypt_response(body["data"], timestamp)
            data = json.loads(decrypted)
            if "uid" in data:
                self.session = session
                return data
        except Exception:
            pass
        return None

    def login(self):
        print("[*] Logging in...")
        for server in self.servers:
            print(f"[*] Trying {server}...")
            result = self._try_login(server)
            if result:
                self.base_url = f"https://{server}"
                print(f"[OK] Login success on {server}, uid={result['uid']}")
                return result["uid"]

        raise Exception("Login failed on all domains")

    def api_get(self, path):
        timestamp = int(time.time())
        resp = self.session.get(
            f"{self.base_url}{path}",
            headers=self._get_api_headers(timestamp),
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        return self._decrypt_response(body["data"], timestamp)

    def api_post(self, path, form_data):
        timestamp = int(time.time())
        resp = self.session.post(
            f"{self.base_url}{path}",
            headers={
                **self._get_api_headers(timestamp),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=form_data,
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        return self._decrypt_response(body["data"], timestamp)

    def daily_check_in(self, uid):
        print("[*] Fetching daily record...")
        record = json.loads(self.api_get(f"/daily?user_id={uid}"))
        if "daily_id" not in record:
            raise Exception(f"Invalid daily_id: {record}")
        daily_id = record["daily_id"]
        print(f"[*] daily_id={daily_id}")

        print("[*] Submitting check-in...")
        result = json.loads(self.api_post("/daily_chk", {
            "user_id": uid,
            "daily_id": daily_id,
        }))
        if "msg" not in result:
            raise Exception(f"Invalid check-in result: {result}")
        return result["msg"]

    def run(self):
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"=== JM Check-In | {today} ===")
        uid = self.login()
        msg = self.daily_check_in(uid)
        print(f"[OK] Check-in result: {msg}")
        return msg


if __name__ == "__main__":
    username = os.environ.get("JM_USERNAME", "")
    password = os.environ.get("JM_PASSWORD", "")
    if not username or not password:
        print("[ERROR] JM_USERNAME and JM_PASSWORD environment variables are required")
        exit(1)

    checker = JMCheckIn(username, password)
    checker.run()
