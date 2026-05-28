# Pica-Jm-Checkin

禁漫天堂 (JM) + Picacg (哔咔) 每日自动签到脚本，通过 GitHub Actions 定时执行。

## 功能

- JM Comic 每日签到
- Picacg 每日签到
- 签到成功/失败 Telegram 通知
- 失败自动重试（Picacg）
- 执行时间随机偏移，降低风控风险

## 部署

### 1. Fork 或上传代码到你的 GitHub 仓库

### 2. 配置 Secrets

到仓库 **Settings → Secrets and variables → Actions**，新建以下 Secrets：

| Secret | 说明 |
|---|---|
| `JM_USERNAME` | JM 账号 |
| `JM_PASSWORD` | JM 密码 |
| `PICACG_USERNAME` | Picacg 账号 |
| `PICACG_PASSWORD` | Picacg 密码 |
| `PICACG_BASE_URL` | Picacg API 地址 (默认 `https://picaapi.go2778.com`) |
| `TG_BOT_TOKEN` | Telegram Bot Token（可选，用于通知） |
| `TG_CHAT_ID` | Telegram Chat ID（可选） |

> 可只配置其中一组签到，脚本会自动跳过未配置的项目。

### 3. 运行

工作流默认每天 0:00 UTC 触发（随机延迟 0-60 分钟后执行），也可手动触发：

到仓库 **Actions** 页 → 选择 **Daily Check-In** → **Run workflow**

## 本地运行

```bash
pip install -r requirements.txt

# JM 签到
JM_USERNAME=your_username JM_PASSWORD=your_password python checkin.py

# Picacg 签到
PICACG_USERNAME=your_username PICACG_PASSWORD=your_password python checkin.py

# 全部
JM_USERNAME=... JM_PASSWORD=... PICACG_USERNAME=... PICACG_PASSWORD=... python checkin.py
```
