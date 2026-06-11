import re

_SCRIPT_TAG_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
_IFRAME_TAG_RE = re.compile(r"<iframe\b[^>]*>.*?</iframe\s*>", re.IGNORECASE | re.DOTALL)
_OBJECT_TAG_RE = re.compile(r"<object\b[^>]*>.*?</object\s*>", re.IGNORECASE | re.DOTALL)
_EMBED_TAG_RE = re.compile(r"<embed\b[^>]*>", re.IGNORECASE | re.DOTALL)
# 匹配跨行和制表符分隔的事件处理器（re.DOTALL 让 . 匹配换行，\s* 覆盖空白字符）
_EVENT_HANDLER_RE = re.compile(
    r"\son\w+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^>\s]+)",
    re.IGNORECASE | re.DOTALL,
)
_JS_PROTOCOL_RE = re.compile(r"javascript:\s*[^\s\"'>]+", re.IGNORECASE)


def sanitize_html(text: str) -> str:
    """移除常见危险 HTML 标签、事件处理器和 javascript: 伪协议。
    re.DOTALL 确保跨行的事件处理器（如 onerror\\n=alert(1)）也能被匹配。
    """
    text = _SCRIPT_TAG_RE.sub("", text)
    text = _IFRAME_TAG_RE.sub("", text)
    text = _OBJECT_TAG_RE.sub("", text)
    text = _EMBED_TAG_RE.sub("", text)
    text = _EVENT_HANDLER_RE.sub("", text)
    text = _JS_PROTOCOL_RE.sub("", text)
    return text
