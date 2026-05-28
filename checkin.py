import os
import sys
import time
import hashlib
import hmac
import json
import uuid
import base64
import requests
from Crypto.Cipher import AES
from datetime import datetime


class Progress:
    def __init__(self, total, title=''):
        self.total = total
        self.current = 0
        self._last = ''
        if title:
            print(f'📋 {title}')

    def bar(self, pct):
        filled = pct // 5
        return '█' * filled + '░' * (20 - filled)

    def update(self, text):
        self.current += 1
        pct = int(self.current / self.total * 100)
        print(f'  ▶ [{self.current}/{self.total}] |{self.bar(pct)}| {pct}% {text}')

    def done(self, text='完成'):
        print(f'  ▶ [{self.total}/{self.total}] |████████████████████| 100% {text}')
        print()

_TC = "經獲幣獎勵連續錄簽過關體認證碼驗動態權確頁稱帳號郵件時間點對爲與個們說話題會發現見來還這麼嗎請問答回覆製圖發關懷準備機當瞭隻從業報麵條匯盡畫書僅廣義標誌導覽瀏覽選項單擊裏"
_SC = "经获币奖励连续录签过关体认证码验动态权确页称号邮件时间点对为与个们说话题会发现见来还这么吗请问答回复制图发关怀准备机当了只从业报面条汇尽画书仅广义标标志导览浏览选项单击里"

def sc(text):
    return text.translate(str.maketrans(_TC, _SC))


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

    def __init__(self, username, password, progress=None):
        self.username = username
        self.password = password
        self.base_url = None
        self.progress = progress
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
        if self.progress:
            self.progress.update(f'JM: 获取 {len(servers)} 个域名')

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
                if self.progress:
                    self.progress.update(f'JM: 登录成功')
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
        return result

    def run(self):
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"=== JM Check-In | {today} ===")
        uid = self.login()
        result = self.daily_check_in(uid)
        msg = result["msg"]
        msg_sc = sc(msg)

        extra = []
        for k in ("exp", "coin", "days", "gold", "silver"):
            if k in result:
                extra.append(f"{k}={result[k]}")
        reward = f" ({', '.join(extra)})" if extra else ""

        line = f"{msg_sc}{reward}"
        print(f"[OK] Check-in result: {line}")
        if self.progress:
            self.progress.update(f'JM: {msg_sc}')
        return line


class PicacgCheckIn:
    API_KEY = "C69BAF41DA5ABD1FFEDC6D2FEA56B"
    HMAC_KEY = b'~d}$Q7$eIni=V)9\\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn'

    def __init__(self, username, password, base_url="https://picaapi.go2778.com", progress=None):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.token = None
        self.progress = progress

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
        if self.progress:
            self.progress.update('Picacg: 登录成功')
        return self.token

    def profile(self):
        _, data = self._req("GET", "/users/profile")
        return data.get("data", {}).get("user", {})

    def is_punched(self):
        return self.profile().get("isPunched", False)

    def punch(self):
        before = self.profile()
        exp_before = before.get("exp", 0)
        level_before = before.get("level", 0)

        if before.get("isPunched"):
            print("[*] Already punched in today, skipping")
            return "already_punched"

        for attempt in range(2):
            print(f"[*] Submitting Picacg punch-in (attempt {attempt + 1})...")
            _, data = self._req("POST", "/users/punch-in", {})
            res = data.get("data", {}).get("res", {})
            status = res.get("status")
            if status == "ok":
                after = self.profile()
                exp_gain = after.get("exp", 0) - exp_before
                parts = [f"punchInLastDay={res.get('punchInLastDay')}"]
                if exp_gain > 0:
                    parts.append(f"exp+{exp_gain}")
                if after.get("level", 0) > level_before:
                    parts.append(f"level up! ({level_before}→{after['level']})")
                line = "签到成功 (" + ", ".join(parts) + ")"
                print(f"[OK] Punch-in result: {line}")
                return line
            if attempt == 0:
                print(f"[WARN] Punch-in failed, retrying...")
        print(f"[WARN] Punch-in result: {res}")
        return f"签到失败 ({res.get('status')})"

    def run(self):
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"=== Picacg Punch-In | {today} ===")
        self.login()
        result = self.punch()
        label = {
            "already_punched": "今日已签到，跳过",
        }.get(result, result)
        if self.progress:
            self.progress.update(f'Picacg: {label}')
        return label


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
    print(f"===== 每日签到 | {today} =====\n")

    total_steps = 0
    jm_user = os.environ.get("JM_USERNAME", "")
    jm_pass = os.environ.get("JM_PASSWORD", "")
    pc_user = os.environ.get("PICACG_USERNAME", "")
    pc_pass = os.environ.get("PICACG_PASSWORD", "")
    pc_url = os.environ.get("PICACG_BASE_URL", "https://picaapi.go2778.com")

    if jm_user and jm_pass: total_steps += 3
    if pc_user and pc_pass: total_steps += 2
    total_steps += 1

    p = Progress(total_steps, '签到流程')

    results = []
    step = 0

    # JM Check-In
    if jm_user and jm_pass:
        try:
            checker = JMCheckIn(jm_user, jm_pass, progress=p)
            msg = checker.run()
            results.append(f"JM: {msg}")
        except Exception as e:
            err = f"JM failed: {e}"
            print(f"\n[ERROR] {err}")
            results.append(err)
    else:
        print("[SKIP] JM_USERNAME/JM_PASSWORD not set")
        results.append("JM: skipped")

    # Picacg Punch-In
    if pc_user and pc_pass:
        try:
            checker = PicacgCheckIn(pc_user, pc_pass, pc_url, progress=p)
            msg = checker.run()
            results.append(f"Picacg: {msg}")
        except Exception as e:
            err = f"Picacg failed: {e}"
            print(f"\n[ERROR] {err}")
            results.append(err)
    else:
        print("[SKIP] PICACG_USERNAME/PICACG_PASSWORD not set")
        results.append("Picacg: skipped")

    p.update('发送通知')
    notify_tg(f"<b>每日签到 | {today}</b>\n" + "\n".join(results))
    p.done()
