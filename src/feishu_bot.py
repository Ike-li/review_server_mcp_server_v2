import json
import logging
from typing import Dict, Any

try:
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import (
        P2ImMessageReceiveV1, ReplyMessageRequest, ReplyMessageRequestBody
    )
except ImportError:
    lark = None

# 这里我们不能直接 import service，因为 server 内部也依赖这里，会产生循环引用。
# 将用回调或者外部注入的方式处理。

logger = logging.getLogger(__name__)

class FeishuBotHandler:
    def __init__(self, service, config):
        self.service = service
        self.config = config
        
        if not lark:
            self.handler = None
            return
            
        self.client = lark.Client.builder() \
            .app_id(config.feishu_app_id) \
            .app_secret(config.feishu_app_secret) \
            .build()
            
        self.handler = lark.EventDispatcherHandler.builder(
            config.feishu_encrypt_key, 
            config.feishu_verification_token, 
            lark.LogLevel.INFO
        ).register_p2_im_message_receive_v1(self._handle_message).build()

    def _do_p1_check(self, text: str) -> str:
        """简单的文本匹配指令示例"""
        text = text.strip()
        if text.startswith("/detect"):
            parts = text.split()
            if len(parts) >= 2:
                game_id = parts[1]
                server_id = parts[2] if len(parts) > 2 else None
                dt = "2026-04-19" # Default for demo today
                try:
                    report = self.service.generate_report(game_id, server_id, dt)
                    return report
                except Exception as e:
                    return f"检测失败: {e}"
            return "用法: /detect <game_id> [server_id] \n比如: /detect 10001 review-10001-appstore-01"
        
        return "你好，我是提审服泄漏检测助手。支持的指令：\n/detect <game_id> [server_id] - 检查游戏泄漏风险"

    def _handle_message(self, data: P2ImMessageReceiveV1) -> None:
        try:
            if data.event.message.message_type == "text":
                content = json.loads(data.event.message.content)
                text = content.get("text", "")
                
                # 处理指令
                reply_text = self._do_p1_check(text)
                
                # 发送回复
                request = ReplyMessageRequest.builder() \
                    .message_id(data.event.message.message_id) \
                    .request_body(ReplyMessageRequestBody.builder()
                        .content(json.dumps({"text": reply_text}))
                        .msg_type("text")
                        .build()) \
                    .build()
                
                self.client.im.v1.message.reply(request)
        except Exception as e:
            logger.error(f"处理消息失败: {e}")

    async def handle_webhook(self, request_body: bytes, headers: Dict[str, str], uri: str) -> Dict[str, Any]:
        """处理 Webhook HTTP 请求"""
        if not self.handler:
            return {"code": 500, "msg": "lark-oapi sdk not installed", "data": ""}
            
        req = lark.BaseRequest()
        req.body = request_body
        req.headers = headers
        req.uri = uri
        
        resp = self.handler.do(req)
        
        return {
            "code": resp.status_code,
            "msg": resp.msg,
            "data": resp.body.decode("utf-8") if resp.body else ""
        }
