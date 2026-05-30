import os, sys, hashlib, hmac, json, uuid, base64, time, requests
from Crypto.Cipher import AES
from urllib.parse import urlencode

def notify_tg(message):
    bot_token = os.environ.get("TG_BOT_TOKEN", "")
    chat_id = os.environ.get("TG_CHAT_ID", "")
    msg_id = os.environ.get("TG_MESSAGE_ID", "")
    if not bot_token or not chat_id:
        return
    try:
        if msg_id:
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/editMessageText",
                json={"chat_id": int(chat_id), "message_id": int(msg_id), "text": message, "parse_mode": "HTML"},
                timeout=10,
            )
        else:
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": int(chat_id), "text": message, "parse_mode": "HTML"},
                timeout=10,
            )
    except Exception:
        pass


def get_jm_info():
    domain_url = "https://rup4a04-c02.tos-cn-hongkong.bytepluses.com/newsvr-2025.txt"
    domain_secret = "diosfjckwpqpdfjkvnqQjsik"
    kjm_secret = "185Hcomic3PAPP7R"
    jm_auth_key = "18comicAPPContent"
    jm_version = "2.0.16"
    fallback = ["www.cdntwice.org", "www.cdnsha.org", "www.cdnaspa.cc", "www.cdnntr.cc"]

    username = os.environ.get("JM_USERNAME", "")
    password = os.environ.get("JM_PASSWORD", "")
    if not username or not password:
        return None

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.0.0 Mobile Safari/537.36"})

    servers = []
    try:
        r = requests.get(domain_url, timeout=10)
        raw = r.content.decode("utf-8-sig").strip()
        key = hashlib.md5(domain_secret.encode()).hexdigest().encode()
        data = base64.b64decode(raw)
        cipher = AES.new(key, AES.MODE_ECB)
        dec = cipher.decrypt(data).decode("utf-8", errors="ignore")
        s = e = 0
        while s < len(dec) and dec[s] not in ("{"): s += 1
        e = len(dec) - 1
        while e > s and dec[e] not in ("}"): e -= 1
        servers = json.loads(dec[s:e+1]).get("Server", [])[:4]
    except:
        pass
    if not servers:
        servers = fallback

    base_headers = {
        "Accept": "*/*", "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9", "Connection": "keep-alive",
        "Origin": "https://localhost", "Referer": "https://localhost/",
        "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "cross-site",
        "X-Requested-With": "com.example.app",
    }

    for server in servers:
        try:
            ts = str(int(time.time()))
            token = hashlib.md5(f"{ts}{jm_auth_key}".encode()).hexdigest()
            headers = {
                **base_headers,
                "Authorization": "Bearer", "token": token, "tokenparam": f"{ts},{jm_version}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            r = session.post(f"https://{server}/login", headers=headers,
                             data=urlencode({"username": username, "password": password}), timeout=15)
            if r.status_code != 200:
                continue
            body = r.json()
            dec_key = hashlib.md5(f"{ts}{kjm_secret}".encode()).hexdigest().encode()
            cipher = AES.new(dec_key, AES.MODE_ECB)
            dec = cipher.decrypt(base64.b64decode(body["data"])).decode("utf-8", errors="ignore")
            s = e = 0
            while s < len(dec) and dec[s] not in ("{"): s += 1
            e = len(dec) - 1
            while e > s and dec[e] not in ("}"): e -= 1
            info = json.loads(dec[s:e+1])

            next_exp = int(info.get("nextLevelExp", 0))
            exp_val = int(info.get("exp", 0))
            exp_pct = min(round(exp_val / next_exp * 100), 100) if next_exp > 0 else 100
            return {
                "uid": info.get("uid", "?"),
                "name": info.get("username", "?"),
                "level": info.get("level", 1),
                "level_name": info.get("level_name", ""),
                "coin": info.get("coin", 0),
                "exp": exp_val,
                "exp_pct": exp_pct,
                "favorites": f"{info.get('album_favorites', 0)}/{info.get('album_favorites_max', 0)}",
            }
        except:
            continue
    return None


def get_pica_info():
    api_key = "C69BAF41DA5ABD1FFEDC6D2FEA56B"
    hmac_key = b'~d}$Q7$eIni=V)9\\RK/P.RM4;9[7|@/CA}b~OW!3?EV`:<>M7pddUBL5n|0/*Cn'
    base_url = os.environ.get("PICACG_BASE_URL", "https://picaapi.go2778.com")

    username = os.environ.get("PICACG_USERNAME", "")
    password = os.environ.get("PICACG_PASSWORD", "")
    if not username or not password:
        return None

    def req(method, path, token="", body=None):
        nonce = uuid.uuid4().hex.replace('-', '')
        ts = str(int(time.time()))
        p = path.lstrip('/')
        raw = (p + ts + nonce + method.upper() + api_key).lower()
        sig = hmac.new(hmac_key, raw.encode(), hashlib.sha256).hexdigest()
        headers = {
            "api-key": api_key, "accept": "application/vnd.picacomic.com.v1+json",
            "app-channel": "3", "authorization": token,
            "time": ts, "nonce": nonce, "app-version": "2.2.1.3.3.4",
            "app-uuid": "defaultUuid", "image-quality": "original",
            "app-platform": "android", "app-build-version": "45",
            "Content-Type": "application/json; charset=UTF-8",
            "user-agent": "okhttp/3.8.1",
            "version": "v1.4.1", "Host": base_url.replace("https://", ""),
            "signature": sig, "Accept-Encoding": "gzip, deflate",
        }
        r = requests.request(method.upper(), f"{base_url}{path}", headers=headers, json=body, timeout=20)
        return r.status_code, r.json()

    try:
        s, d = req("POST", "/auth/sign-in", "", {"email": username, "password": password})
        if s != 200 or d.get("code") != 200:
            return None
        token = d["data"]["token"]

        s, d = req("GET", "/users/profile", token)
        user = d.get("data", {}).get("user", {})

        next_exp = user.get("nextLevelExp", 0)
        exp_pct = min(round(user.get("exp", 0) / next_exp * 100), 100) if next_exp > 0 else 100
        return {
            "name": user.get("name", "?"),
            "email": user.get("email", "?"),
            "level": user.get("level", 1),
            "title": user.get("title", ""),
            "exp": user.get("exp", 0),
            "exp_pct": exp_pct,
            "gender": user.get("gender", "?"),
            "isPunched": user.get("isPunched", False),
        }
    except:
        return None


if __name__ == "__main__":
    today = time.strftime("%Y-%m-%d", time.gmtime())

    lines = [f"<b>👤 账号信息 | {today}</b>\n"]

    jm = get_jm_info()
    if jm:
        pct = jm.get("exp_pct", 0)
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lines.append(
            f"<b>📖 JM Comic</b>\n"
            f"  👤 {jm['name']} (UID {jm['uid']})\n"
            f"  ⭐ Lv.{jm['level']} ({jm['level_name']})\n"
            f"  ✨ {jm['exp']} 经验\n"
            f"  💰 {jm['coin']} 金币\n"
            f"  ❤️ 收藏 {jm['favorites']}\n"
            f"  📈 |{bar}| {pct}%"
        )
    else:
        lines.append("<b>📖 JM</b> ❌ 未配置或登录失败")

    lines.append("")

    pica = get_pica_info()
    if pica:
        punched = "✅" if pica["isPunched"] else "❌"
        lines.append(
            f"<b>🐱 Picacg</b>\n"
            f"  👤 {pica['name']} ({pica['email']})\n"
            f"  ⭐ Lv.{pica['level']} ({pica['title']})\n"
            f"  ✨ {pica['exp']} 经验\n"
            f"  📌 今日签到: {punched}"
        )
    else:
        lines.append("<b>🐱 Picacg</b> ❌ 未配置或登录失败")

    msg = "\n".join(lines)
    print(msg)
    notify_tg(msg)
