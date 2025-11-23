import asyncio
import base64
import io
from typing import Optional
import aiohttp
from PIL import Image as PILImage

from astrbot.api import logger
from astrbot.api.star import Context, Star, register
from astrbot.api.event.filter import event_message_type, EventMessageType
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.message.components import Image, At, Reply


class ImageWorkflow:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def _download_image(self, url: str) -> Optional[bytes]:
        try:
            async with self.session.get(url) as resp:
                resp.raise_for_status()
                return await resp.read()
        except Exception as e:
            logger.error(f"图片下载失败: {e}")
            return None

    async def _get_avatar(self, user_id: str) -> Optional[bytes]:
        if not user_id.isdigit():
            import random

            user_id = "".join(random.choices("0123456789", k=9))
        avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
        try:
            async with self.session.get(avatar_url, timeout=10) as resp:
                resp.raise_for_status()
                return await resp.read()
        except Exception as e:
            logger.error(f"下载头像失败: {e}")
            return None

    def _extract_first_frame_sync(self, raw: bytes) -> bytes:
        try:
            img_io = io.BytesIO(raw)
            img = PILImage.open(img_io)
            if img.format != "GIF":
                return raw
            first_frame = img.convert("RGBA")
            out_io = io.BytesIO()
            first_frame.save(out_io, format="PNG")
            return out_io.getvalue()
        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            return raw

    async def _load_bytes(self, src: str) -> Optional[bytes]:
        raw: Optional[bytes] = None
        loop = asyncio.get_running_loop()

        if src.startswith("http"):
            raw = await self._download_image(src)
        elif src.startswith("base64://"):
            raw = await loop.run_in_executor(None, base64.b64decode, src[9:])

        if not raw:
            return None
        return await loop.run_in_executor(None, self._extract_first_frame_sync, raw)

    async def get_first_image(self, event: AstrMessageEvent) -> Optional[bytes]:
        # 优先处理 Reply 中的图片
        for seg in event.message_obj.message:
            if isinstance(seg, Reply) and hasattr(seg, "chain") and seg.chain:
                for sub_seg in seg.chain:
                    if isinstance(sub_seg, Image):
                        if sub_seg.url and (img := await self._load_bytes(sub_seg.url)):
                            return img
                        if sub_seg.file and (img := await self._load_bytes(sub_seg.file)):
                            return img

        # 然后处理消息中的图片和 At
        for seg in event.message_obj.message:
            if isinstance(seg, Image):
                if seg.url and (img := await self._load_bytes(seg.url)):
                    return img
                if seg.file and (img := await self._load_bytes(seg.file)):
                    return img
            elif isinstance(seg, At):
                if avatar := await self._get_avatar(str(seg.qq)):
                    return avatar

        # 最后使用发送者头像
        return await self._get_avatar(event.get_sender_id())

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


@register(
    "astrbot_plugin_generic_image_gen",
    "mkroen",
    "通用图片生成插件",
    "0.1.0",
    "https://github.com/mkroen/astrbot_plugin_generic_image_gen",
)
class GenericImageGenPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.api_keys = self.config.get("api_keys", [])
        self.current_key_index = 0
        self.api_base_url = self.config.get("api_base_url", "")

        # 基础生图配置
        self.basic_gen_config = self.config.get(
            "basic_generation", {"enabled": True, "trigger": "生图", "model": "", "negative_prompt": ""}
        )

        # 直接使用配置中的指令列表
        self.commands_config = self.config.get("commands", [])

        self.iwf = ImageWorkflow()

    async def terminate(self):
        await self.iwf.close()

    @event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        message_str = event.message_str.strip()

        # 检查基础生图指令
        if self.basic_gen_config.get("enabled", True):
            trigger = self.basic_gen_config.get("trigger", "生图")
            if message_str.startswith(trigger):
                user_prompt = message_str[len(trigger) :].strip() or " "
                model = self.basic_gen_config.get("model") or None
                negative_prompt = self.basic_gen_config.get("negative_prompt") or None

                async for result in self._handle_generation(
                    event,
                    prompt=user_prompt,
                    negative_prompt=negative_prompt,
                    model=model,
                ):
                    yield result
                return

        # 检查自定义指令
        for cmd_config in self.commands_config:
            trigger = cmd_config.get("trigger")
            if not trigger:
                continue

            if message_str.startswith(trigger) or message_str == trigger:
                fixed_prompt = cmd_config.get("prompt", "")
                negative_prompt = cmd_config.get("negative_prompt", "")
                model = cmd_config.get("model")

                async for result in self._handle_generation(
                    event,
                    prompt=fixed_prompt,
                    negative_prompt=negative_prompt,
                    model=model,
                ):
                    yield result
                return

    async def _handle_generation(
        self,
        event: AstrMessageEvent,
        prompt: str,
        negative_prompt: Optional[str] = None,
        model: Optional[str] = None,
    ):
        image_bytes = await self.iwf.get_first_image(event)
        yield event.plain_result("正在生成中，请稍候...")

        try:
            result_bytes = await self._generate_with_api(image_bytes, prompt, negative_prompt, model)

            if isinstance(result_bytes, bytes):
                yield event.chain_result([Image.fromBytes(result_bytes)])
            elif isinstance(result_bytes, str):
                yield event.plain_result(f"生成失败: {result_bytes}")
            else:
                yield event.plain_result("生成失败，未返回图片。")

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            yield event.plain_result(f"生成出错: {e}")

    async def _generate_with_api(
        self, image_bytes: Optional[bytes], prompt: str, negative_prompt: Optional[str], model: Optional[str]
    ) -> bytes | str | None:
        async def api_operation(api_key: str):
            payload = {"prompt": prompt}

            if negative_prompt:
                payload["negative_prompt"] = negative_prompt
            if model:
                payload["model"] = model

            if image_bytes:
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                payload["image"] = image_base64

            return await self._send_api_request(payload, api_key)

        result = await self._with_retry(api_operation)
        return result if result else "所有API密钥均尝试失败"

    async def _send_api_request(self, payload: dict, api_key: str):
        base_url = self.api_base_url.strip().removesuffix("/")
        endpoint = f"{base_url}/v1/images/generations"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        async with self.iwf.session.post(url=endpoint, json=payload, headers=headers) as response:
            if response.status != 200:
                response_text = await response.text()
                logger.error(f"API请求失败: HTTP {response.status}, 响应: {response_text}")
                response.raise_for_status()
            data = await response.json()

        if "data" in data and len(data["data"]) > 0:
            if "url" in data["data"][0]:
                image_url = data["data"][0]["url"]
                return await self.iwf._download_image(image_url)
            elif "b64_json" in data["data"][0]:
                b64_string = data["data"][0]["b64_json"].strip()
                missing_padding = len(b64_string) % 4
                if missing_padding:
                    b64_string += "=" * (4 - missing_padding)
                return base64.b64decode(b64_string)

        raise Exception("操作成功，但未在响应中获取到图片数据")

    def _get_current_key(self):
        if not self.api_keys:
            return None
        return self.api_keys[self.current_key_index]

    def _switch_key(self):
        if not self.api_keys:
            return
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"切换到下一个 API 密钥（索引：{self.current_key_index}）")

    async def _with_retry(self, operation, *args, **kwargs):
        max_attempts = len(self.api_keys)
        if max_attempts == 0:
            return None

        for attempt in range(max_attempts):
            current_key = self._get_current_key()
            logger.info(f"尝试操作（密钥索引：{self.current_key_index}，次数：{attempt + 1}/{max_attempts}）")
            try:
                return await operation(current_key, *args, **kwargs)
            except Exception as e:
                logger.error(f"第{attempt + 1}次尝试失败：{str(e)}")
                if attempt < max_attempts - 1:
                    self._switch_key()
                else:
                    logger.error("所有API密钥均尝试失败")
        return None
