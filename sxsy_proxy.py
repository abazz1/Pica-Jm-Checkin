import os
import re
import json
import requests as _req


def patch_requests():
    pu = os.environ.get('SXSY_PROXY_URL', '')
    pt = os.environ.get('SXSY_PROXY_TOKEN', '')
    if not pu:
        return

    _orig_session = _req.Session
    _orig_get = _req.get
    _orig_post = _req.post

    class ProxySession(_orig_session):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self._proxy_url = pu

        def request(self, method, url, **kwargs):
            if not re.match(r'https?://(sxsy\d+\.(com|org)|sxsy\.org)/', url):
                return super().request(method, url, **kwargs)

            payload = {
                'url': url,
                'method': method,
                'headers': dict(kwargs.get('headers', {})),
            }
            cookie_str = '; '.join(f'{k}={v}' for k, v in self.cookies.items())
            if cookie_str:
                payload['cookieStr'] = cookie_str
            if 'data' in kwargs:
                payload['body'] = kwargs['data']

            r = _orig_post(self._proxy_url, json=payload,
                           headers={'X-Proxy-Token': pt, 'Content-Type': 'application/json'},
                           timeout=60)
            result = r.json()

            for c in result.get('setCookie', []):
                parts = c.split(';')[0].strip().split('=', 1)
                if len(parts) == 2:
                    self.cookies.set(parts[0], parts[1])

            class _Resp:
                def __init__(self, status, text, headers):
                    self.status_code = status
                    self.text = text
                    self.content = text.encode()
                    self.headers = headers

                def json(self):
                    return json.loads(self.text)

            return _Resp(result['status'], result['body'], result.get('headers', {}))

    def _check_domain(url):
        return bool(re.match(r'https?://(sxsy\d+\.(com|org)|sxsy\.org)/', url))

    def _proxy_get(url, **kw):
        if _check_domain(url):
            return ProxySession().get(url, **kw)
        return _orig_get(url, **kw)

    def _proxy_post(url, **kw):
        if _check_domain(url):
            return ProxySession().post(url, **kw)
        return _orig_post(url, **kw)

    _req.Session = ProxySession
    _req.get = _proxy_get
    _req.post = _proxy_post
