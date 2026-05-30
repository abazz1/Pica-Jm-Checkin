import os, sys, hashlib, hmac, json, uuid, base64, time, random, requests
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


try:
    import sxsy_proxy
    sxsy_proxy.patch_requests()
except:
    pass


def get_sxsy_info():
    sxsy_env = os.environ.get("SXSY", "")
    if not sxsy_env:
        return None

    import requests as req
    host = "sxsy13.com"
    try:
        r = req.get('https://sxsy.org/site.jpg', timeout=10)
        import ddddocr
        text = ddddocr.DdddOcr(show_ad=False).classification(r.content).lower().replace(' ', '')
        import re
        m = re.search(r'(sxsy\d+\.?com)', text)
        if m:
            h = m.group(1).replace('。', '.').replace('，', '.')
            if '.' not in h:
                h = h.replace('com', '.com')
            host = h
    except:
        pass

    accounts = []
    for line in sxsy_env.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if '&' in line:
            accounts.append(line.split('&', 1))
        else:
            accounts.append((line, None))

    lines = []
    for idx, (user, pwd) in enumerate(accounts, 1):
        session = req.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        try:
            session.get(f"https://{host}/", timeout=20)
        except Exception as e:
            lines.append(f"  👤 SXSY 账号{idx}: ❌ 连接失败 ({host}, {e})")
            continue

        cookie_file = 'sxsy_checkin_cookie.json'
        cookies_ok = False
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file) as f:
                    data = json.load(f)
                if user in data.get('accounts', {}):
                    for item in data['accounts'][user]['cookies'].split(';'):
                        if '=' in item:
                            k, v = item.split('=', 1)
                            session.cookies.set(k.strip(), v.strip())
                    r = session.get(f"https://{host}/home.php?mod=space", timeout=20)
                    if '请先登录' not in r.text:
                        cookies_ok = True
            except:
                pass

        if not cookies_ok and pwd:
            try:
                r = session.get(f"https://{host}/member.php?mod=logging&action=login&infloat=yes&frommessage&inajax=1&ajaxtarget=messagelogin", timeout=20)
                if r.status_code != 200 or len(r.text) < 100:
                    lines.append(f"  👤 SXSY 账号{idx}: ❌ Cloudflare 拦截 (HTTP {r.status_code})")
                    continue
                formhash = re.search(r'formhash" value="([^"]+)"', r.text)
                seccodehash = re.search(r'seccode_([a-zA-Z0-9]{6})', r.text)
                loginhash = re.search(r'main_messaqge_([a-zA-Z0-9]{5})', r.text)
                if not all([formhash, seccodehash, loginhash]):
                    snippet = r.text[:200].replace('\n', ' ')
                    lines.append(f"  👤 SXSY 账号{idx}: ❌ 获取参数失败 (HTTP {r.status_code}, {snippet})")
                    continue

                ocr = ddddocr.DdddOcr(show_ad=False)
                for _ in range(5):
                    cu = f"https://{host}/misc.php?mod=seccode&update={random.randint(10000,99999)}&idhash={seccodehash.group(1)}"
                    r2 = session.get(cu, headers={'Referer': f'https://{host}/member.php?mod=logging&action=login'}, timeout=20)
                    cap = ocr.classification(r2.content)
                    vu = f"https://{host}/misc.php?mod=seccode&action=check&inajax=1&modid=member::logging&idhash={seccodehash.group(1)}&secverify={cap}"
                    r3 = session.get(vu, headers={'Referer': f'https://{host}/member.php?mod=logging&action=login'}, timeout=20)
                    if 'succeed' in r3.text:
                        break
                else:
                    lines.append(f"  👤 SXSY 账号{idx}: ❌ 验证码失败")
                    continue

                import urllib.parse
                loginfield = 'email' if '@' in user else 'username'
                payload = f"formhash={formhash.group(1)}&referer=https://{host}/&loginfield={loginfield}&username={user}&password={pwd}&questionid=0&answer=&seccodehash={seccodehash.group(1)}&seccodemodid=member::logging&seccodeverify={cap}&cookietime=2592000"
                lurl = f"https://{host}/member.php?mod=logging&action=login&loginsubmit=yes&loginhash={loginhash.group(1)}&inajax=1"
                r = session.post(lurl, headers={'Referer': f'https://{host}/', 'content-type': 'application/x-www-form-urlencoded'}, data=urllib.parse.quote(payload, safe='=&'), timeout=20)
                if '欢迎您回来' not in r.text:
                    lines.append(f"  👤 SXSY 账号{idx}: ❌ 登录失败")
                    continue
            except Exception as e:
                lines.append(f"  👤 SXSY 账号{idx}: ❌ {e}")
                continue

        try:
            r = session.get(f"https://{host}/home.php?mod=spacecp&ac=credit&showcredit=1", timeout=20)
            m_money = re.search(r'金钱: </em>(\d+)', r.text)
            m_uid = re.search(r'uid=(\d+)', r.text)
            uid = m_uid.group(1) if m_uid else '?'
            name = re.search(r'欢迎您回来[，,]?\s*([^，,<]+)', r.text)
            display_name = name.group(1).strip() if name else f"账号{idx}"
            money = m_money.group(1) if m_money else '?'
            lines.append(f"  👤 SXSY {display_name} (UID {uid})  💰 {money} 金钱")
        except Exception as e:
            lines.append(f"  👤 SXSY 账号{idx}: ❌ 获取信息失败")
            continue

    return '\n'.join(lines) if lines else None


def pica_exp_progress(level, exp):
    n = int(level)
    e = int(exp)
    if n <= 0:
        return 0
    prev_exp = 0 if n <= 1 else 100 * n * (n - 1)
    next_exp = 100 * (n + 1) * n
    range_exp = next_exp - prev_exp
    if range_exp <= 0:
        return 100
    return min(max(round((e - prev_exp) / range_exp * 100), 0), 100)


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
        pct = pica_exp_progress(pica["level"], pica["exp"])
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        punched = "✅" if pica["isPunched"] else "❌"
        lines.append(
            f"<b>🐱 Picacg</b>\n"
            f"  👤 {pica['name']} ({pica['email']})\n"
            f"  ⭐ Lv.{pica['level']} ({pica['title']})\n"
            f"  ✨ {pica['exp']} 经验\n"
            f"  📌 今日签到: {punched}\n"
            f"  📈 |{bar}| {pct}%"
        )
    else:
        lines.append("<b>🐱 Picacg</b> ❌ 未配置或登录失败")

    lines.append("")

    sxsy = get_sxsy_info()
    if sxsy:
        lines.append(f"<b>📚 尚香书苑</b>\n{sxsy}")
    else:
        lines.append("<b>📚 尚香书苑</b> ❌ 未配置或登录失败")

    msg = "\n".join(lines)
    print(msg)
    notify_tg(msg)
