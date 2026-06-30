"""Azure 语音合成(TTS):把文本合成为自然语音 MP3。

配置(放在 .env):
  AZURE_SPEECH_KEY     Azure 语音服务密钥
  AZURE_SPEECH_REGION  区域,如 eastasia / eastus
  AZURE_SPEECH_VOICE   声音名,默认 zh-CN-XiaoxiaoNeural(温柔女声)
未配置时前端自动回退到浏览器内置 TTS。
"""
import os

import httpx

SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY", "")
SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION", "")
SPEECH_VOICE = os.environ.get("AZURE_SPEECH_VOICE", "zh-CN-XiaoxiaoNeural")


def is_enabled() -> bool:
    return bool(SPEECH_KEY and SPEECH_REGION)


def _escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def synthesize(text: str) -> bytes:
    """返回 MP3 音频字节;失败抛异常。"""
    url = f"https://{SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    ssml = (
        f"<speak version='1.0' xml:lang='zh-CN'>"
        f"<voice name='{SPEECH_VOICE}'>{_escape(text)}</voice></speak>"
    )
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
        "User-Agent": "xiaoweidai",
    }
    resp = httpx.post(url, content=ssml.encode("utf-8"), headers=headers, timeout=30.0)
    resp.raise_for_status()
    return resp.content
