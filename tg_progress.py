import os, sys, json, urllib.request

def tg_progress(step, total, text):
    bt = os.environ.get('TG_BOT_TOKEN', '')
    ci = os.environ.get('TG_CHAT_ID', '')
    mi = os.environ.get('TG_MESSAGE_ID', '')
    if not bt or not ci or not mi:
        return
    pct = int(step / total * 100)
    bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
    msg = f'<b>每日签到</b>\n\n进度 |{bar}| {pct}%\n[{step}/{total}] {text}'
    data = json.dumps({'chat_id': int(ci), 'message_id': int(mi), 'text': msg, 'parse_mode': 'HTML'}).encode()
    try:
        urllib.request.urlopen(f'https://api.telegram.org/bot{bt}/editMessageText', data)
    except:
        pass

if __name__ == '__main__':
    tg_progress(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
