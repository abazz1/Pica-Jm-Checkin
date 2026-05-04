# JM 自动签到

禁漫天堂每日自动签到脚本，通过 GitHub Actions 在每天 0:00 (UTC) 自动执行。

## 功能

- 自动获取最新可用域名
- 自动登录并签到
- 签到失败时自动切换域名重试
- 通过 GitHub Actions 定时运行

## 部署

### 1. Fork 或上传代码到你的 GitHub 仓库

### 2. 配置 Secrets

到仓库 **Settings → Secrets and variables → Actions**，新建以下 Secrets：

| Secret | 说明 |
|---|---|
| `JM_USERNAME` | 账号 |
| `JM_PASSWORD` | 密码 |

### 3. 运行

工作流默认每天 0:00 (UTC) 自动运行，也可手动触发：

到仓库 **Actions** 页 → 选择 **JM Daily Check-In** → **Run workflow**

## 本地运行

```bash
pip install -r requirements.txt
JM_USERNAME=your_username JM_PASSWORD=your_password python checkin.py
```
