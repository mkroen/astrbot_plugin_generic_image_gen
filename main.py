import asyncio
import base64
import io
from typing import Optional
import aiohttp
from PIL import Image as PILImage

from astrbot.api import logger
from astrbot.api.event import filter
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
            return None
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
        # Iterate over components
        for seg in event.message_obj.message:
            if isinstance(seg, Image):
                if seg.url and (img := await self._load_bytes(seg.url)):
                    return img
                if seg.file and (img := await self._load_bytes(seg.file)):
                    return img
            elif isinstance(seg, At):
                if avatar := await self._get_avatar(str(seg.qq)):
                    return avatar
            elif isinstance(seg, Reply):
                if hasattr(seg, "chain") and seg.chain:
                    for sub_seg in seg.chain:
                        if isinstance(sub_seg, Image):
                            if sub_seg.url and (img := await self._load_bytes(sub_seg.url)):
                                return img
        return None

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
        self.commands_config = self.config.get("commands", [])
        self.iwf = ImageWorkflow()

    async def terminate(self):
        await self.iwf.close()

    @filter.command("生图")
    async def generate_image_cmd(self, event: AstrMessageEvent, prompt: str = ""):
        """
        生图 [prompt]
        """
        if not prompt:
            prompt = " "

        async for result in self._handle_generation(event, prompt, use_config_prompt=False):
            yield result

    @event_message_type(EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        message_str = event.message_str.strip()

        for cmd_config in self.commands_config:
            trigger = cmd_config.get("trigger")
            if not trigger:
                continue

            if message_str.startswith(trigger) or message_str == trigger:
                fixed_prompt = cmd_config.get("prompt", "")
                negative_prompt = cmd_config.get("negative_prompt", "")
                model = cmd_config.get("model")
                provider = cmd_config.get("provider")

                async for result in self._handle_generation(
                    event,
                    prompt=fixed_prompt,
                    negative_prompt=negative_prompt,
                    model=model,
                    provider=provider,
                    use_config_prompt=True,
                ):
                    yield result
                return

    async def _handle_generation(
        self,
        event: AstrMessageEvent,
        prompt: str,
        negative_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        use_config_prompt: bool = False,
    ):
        # 1. Extract Image
        image_bytes = await self.iwf.get_first_image(event)

        input_images = None
        if image_bytes:
            b64_str = base64.b64encode(image_bytes).decode("utf-8")
            input_images = [f"base64://{b64_str}"]

        yield event.plain_result("正在生成中，请稍候...")

        try:
            options = {}
            if negative_prompt:
                options["negative_prompt"] = negative_prompt
            if model:
                options["model"] = model

            target_provider = None
            if provider:
                target_provider = self.context.provider_manager.get_provider(provider)  # type: ignore

            result = await self.context.image_generation(  # type: ignore
                prompt=prompt, images=input_images, options=options, provider=target_provider
            )

            if result and result.images:
                images = [Image.fromURL(url) for url in result.images]
                yield event.chain_result(images)  # type: ignore
            else:
                yield event.plain_result("生成失败，未返回图片。")

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            yield event.plain_result(f"生成出错: {e}")
