import requests
import json
import os

# -------------------------------------------------------------------------------------------
# 环境变量说明:
# COOKIES: GLaDOS 账号 cookie，多账号用 & 分隔
# TG_BOT_TOKEN: Telegram Bot Token (可选)
# TG_CHAT_ID: Telegram Chat ID (可选)
# -------------------------------------------------------------------------------------------

def send_telegram_message(bot_token, chat_id, title, content):
    """
    发送 Telegram 消息

    Args:
        bot_token: Telegram Bot Token
        chat_id: Telegram Chat ID
        title: 消息标题
        content: 消息内容

    Returns:
        bool: 发送是否成功
    """
    try:
        # 格式化消息内容（使用 Markdown）
        message = f"🤖 *{title}*\n\n{content}"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True  # 禁用链接预览
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Telegram 推送成功")
            return True
        else:
            print(f"❌ Telegram 推送失败: {response.status_code}, {response.text}")
            return False

    except Exception as e:
        print(f"⚠️ Telegram 推送异常: {str(e)}")
        return False

# -------------------------------------------------------------------------------------------
# github workflows
# -------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # Telegram 推送配置
    tg_bot_token = os.environ.get("TG_BOT_TOKEN", "")
    tg_chat_id = os.environ.get("TG_CHAT_ID", "")

    # 推送内容
    title = ""
    success, fail, repeats = 0, 0, 0        # 成功账号数量 失败账号数量 重复签到账号数量
    context = ""
    account_details = []  # 存储每个账号的详细信息

    # glados账号cookie 直接使用数组 如果使用环境变量需要字符串分割一下
    cookies = os.environ.get("COOKIES", []).split("&")
    if cookies[0] != "":

        check_in_url = "https://glados.space/api/user/checkin"        # 签到地址
        status_url = "https://glados.space/api/user/status"          # 查看账户状态

        referer = 'https://glados.space/console/checkin'
        origin = "https://glados.space"
        useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        payload = {
            'token': 'glados.one'
        }
        
        for cookie in cookies:
            checkin = requests.post(check_in_url, headers={'cookie': cookie, 'referer': referer, 'origin': origin,
                                    'user-agent': useragent, 'content-type': 'application/json;charset=UTF-8'}, data=json.dumps(payload))
            state = requests.get(status_url, headers={
                                'cookie': cookie, 'referer': referer, 'origin': origin, 'user-agent': useragent})

            message_status = ""
            points = 0
            message_days = ""
            status_icon = ""  # 状态图标


            if checkin.status_code == 200:
                # 解析返回的json数据
                result = checkin.json()
                # 获取签到结果
                check_result = result.get('message')
                points = result.get('points')

                # 获取账号当前状态
                result = state.json()
                # 获取剩余时间
                leftdays = int(float(result['data']['leftDays']))
                # 获取账号email
                email = result['data']['email']

                print(check_result)
                if "Checkin! Got" in check_result:
                    success += 1
                    status_icon = "✅"
                    message_status = f"签到成功，会员点数 +{points}"
                elif "Checkin Repeats!" in check_result:
                    repeats += 1
                    status_icon = "🔁"
                    message_status = "重复签到，明天再来"
                else:
                    fail += 1
                    status_icon = "❌"
                    message_status = "签到失败，请检查..."

                if leftdays is not None:
                    message_days = f"{leftdays} 天"
                else:
                    message_days = "error"
            else:
                email = ""
                status_icon = "❌"
                message_status = "签到请求URL失败, 请检查..."
                message_days = "error"

            # 保存账号详细信息
            account_info = {
                "email": email,
                "status_icon": status_icon,
                "status": message_status,
                "points": points,
                "leftdays": message_days
            }
            account_details.append(account_info)

            context += "账号: " + email + ", P: " + str(points) +", 剩余: " + message_days + " | "

        # 推送内容
        title = f'GLaDOS 签到报告'

        # 构建美化的推送内容
        context = f"📊 *签到统计*\n"
        context += f"✅ 成功: {success} | 🔁 重复: {repeats} | ❌ 失败: {fail}\n\n"
        context += f"📋 *账号详情*\n"
        context += "━━━━━━━━━━━━━━━━\n"

        for idx, account in enumerate(account_details, 1):
            context += f"\n*账号 {idx}*\n"
            context += f"{account['status_icon']} {account['status']}\n"
            if account['email']:
                context += f"📧 {account['email']}\n"
            if account['points'] > 0:
                context += f"💎 点数: {account['points']}\n"
            context += f"⏰ 剩余: {account['leftdays']}\n"

        print("Send Content:" + "\n", context)
        
    else:
        # 推送内容 
        title = f'# 未找到 cookies!'

    print("cookies:", cookies)
    print("tg_bot_token:", "已配置" if tg_bot_token else "未配置")
    print("tg_chat_id:", "已配置" if tg_chat_id else "未配置")

    # 推送消息 - Telegram
    if not tg_bot_token or not tg_chat_id:
        print("未配置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过 Telegram 推送")
    else:
        send_telegram_message(tg_bot_token, tg_chat_id, title, context)
