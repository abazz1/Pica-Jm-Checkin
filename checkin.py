import os
import time
import hashlib
import hmac
import json
import uuid
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


class PicacgCheckIn:
    API_KEY = "C69BAF41DA5ABD1FFEDC6D2FEA56B"
    HMAC_KEY = b'~d}$Q7$eIni=V)9\\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn'

    def __init__(self, username, password, base_url="https://picaapi.go2778.com"):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.token = None

    def _sign(self, method, path, ts, nonce):
        raw = (path.lstrip('/') + ts + nonce + method.upper() + self.API_KEY).lower()
        return hmac.new(self.HMAC_KEY, raw.encode(), hashlib.sha256).hexdigest()

    def _headers(self, method, path, ts, nonce):
        return {
            "api-key": self.API_KEY,
            "accept": "application/vnd.picacomic.com.v1+json",
            "app-channel": "3",
            "authorization": self.token or "",
            "time": ts,
            "nonce": nonce,
            "app-version": "2.2.1.3.3.4",
            "app-uuid": "defaultUuid",
            "image-quality": "original",
            "app-platform": "android",
            "app-build-version": "45",
            "Content-Type": "application/json; charset=UTF-8",
            "user-agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36",
            "version": "v1.4.1",
            "Host": self.base_url.replace("https://", ""),
            "signature": self._sign(method, path, ts, nonce),
            "Accept-Encoding": "gzip, deflate",
        }

    def _req(self, method, path, body=None):
        nonce = uuid.uuid4().hex.replace('-', '')
        ts = str(int(time.time()))
        r = requests.request(
            method.upper(), f"{self.base_url}{path}",
            headers=self._headers(method, path, ts, nonce),
            json=body, timeout=20,
        )
        return r.status_code, r.json()

    def login(self):
        print("[*] Logging in to Picacg...")
        status, data = self._req("POST", "/auth/sign-in", {
            "email": self.username,
            "password": self.password,
        })
        if status != 200 or data.get("code") != 200:
            raise Exception(f"Login failed: {data}")
        self.token = data["data"]["token"]
        print(f"[OK] Picacg login success")
        return self.token

    def is_punched(self):
        _, data = self._req("GET", "/users/profile")
        return data.get("data", {}).get("user", {}).get("isPunched", False)

    def punch(self):
        if self.is_punched():
            print("[*] Already punched in today, skipping")
            return "already_punched"
        print("[*] Submitting Picacg punch-in...")
        _, data = self._req("POST", "/users/punch-in", {})
        res = data.get("data", {}).get("res", {})
        status = res.get("status")
        if status == "ok":
            print(f"[OK] Punch-in success: {res.get('punchInLastDay')}")
            return "ok"
        print(f"[WARN] Punch-in result: {res}")
        return status

    def run(self):
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"=== Picacg Punch-In | {today} ===")
        self.login()
        result = self.punch()
        print(f"[OK] Punch-in result: {result}")
        return result


def notify_tg(message):
    bot_token = os.environ.get("TG_BOT_TOKEN", "")
    chat_id = os.environ.get("TG_CHAT_ID", "")
    if not bot_token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception:
        pass


if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"===== Daily Check-In | {today} =====\n")

    results = []

    # JM Check-In
    jm_user = os.environ.get("JM_USERNAME", "")
    jm_pass = os.environ.get("JM_PASSWORD", "")
    if jm_user and jm_pass:
        try:
            checker = JMCheckIn(jm_user, jm_pass)
            msg = checker.run()
            results.append(f"JM: {msg}")
        except Exception as e:
            err = f"JM failed: {e}"
            print(f"[ERROR] {err}")
            results.append(err)
    else:
        print("[SKIP] JM_USERNAME/JM_PASSWORD not set")
        results.append("JM: skipped")

    print()

    # Picacg Punch-In
    pc_user = os.environ.get("PICACG_USERNAME", "")
    pc_pass = os.environ.get("PICACG_PASSWORD", "")
    pc_url = os.environ.get("PICACG_BASE_URL", "https://picaapi.go2778.com")
    if pc_user and pc_pass:
        try:
            checker = PicacgCheckIn(pc_user, pc_pass, pc_url)
            msg = checker.run()
            results.append(f"Picacg: {msg}")
        except Exception as e:
            err = f"Picacg failed: {e}"
            print(f"[ERROR] {err}")
            results.append(err)
    else:
        print("[SKIP] PICACG_USERNAME/PICACG_PASSWORD not set")
        results.append("Picacg: skipped")

    print(f"\n===== Done =====")

    notify_tg(f"<b>Daily Check-In | {today}</b>\n" + "\n".join(results))
