"""飞书机器人 Webhook 通知"""

import json
import urllib.request
import urllib.error

def send_feishu_alert(webhook_url: str, title: str, text: str) -> bool:
    """
    发送飞书富文本消息
    
    Args:
        webhook_url: 飞书机器人的 Webhook URL
        title: 消息标题
        text: 消息正文（支持飞书 markdown）
        
    Returns:
        bool: 发送是否成功
    """
    if not webhook_url:
        return False
        
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [
                        [
                            {
                                "tag": "text",
                                "text": text
                            }
                        ]
                    ]
                }
            }
        }
    }
    
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8")
    
    try:
        req = urllib.request.Request(webhook_url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = response.read().decode("utf-8")
            res_json = json.loads(res_data)
            return res_json.get("code", -1) == 0
    except Exception as e:
        print(f"Error sending Feishu alert: {e}")
        return False
