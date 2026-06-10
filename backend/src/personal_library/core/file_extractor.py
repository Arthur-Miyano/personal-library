import os
import re
import zipfile
from io import BytesIO


def extract_text(file_bytes: bytes, filename: str) -> str:
    """根据扩展名提取文本。支持 .txt .md .html .epub .pdf .docx"""
    ext = os.path.splitext(filename)[1].lower()

    if ext in (".txt", ".md"):
        return _decode_text(file_bytes, filename)
    elif ext == ".html":
        return _strip_tags(file_bytes)
    elif ext == ".epub":
        return _extract_epub(file_bytes)
    elif ext == ".pdf":
        return _extract_pdf(file_bytes)
    elif ext == ".docx":
        return _extract_docx(file_bytes)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


ALLOWED_EXTENSIONS = {".txt", ".md", ".html", ".epub", ".pdf", ".docx"}


def _decode_text(raw: bytes, filename: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        import chardet
        result = chardet.detect(raw)
        if result["encoding"] and result["confidence"] > 0.5:
            return raw.decode(result["encoding"])
    except Exception:
        pass
    try:
        return raw.decode("gb18030")
    except Exception:
        pass
    raise ValueError(f"无法识别文件编码: {filename}")


def _strip_tags(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def _html_to_text(html: str) -> str:
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<[^>]+>", "", html)
    return html


def _extract_epub(raw: bytes) -> str:
    # 方式1: ebooklib
    try:
        from ebooklib import epub
        book = epub.read_epub(BytesIO(raw))
        parts: list[str] = []
        for item in book.get_items_of_type(9):
            content = item.get_content().decode("utf-8", errors="replace")
            parts.append(_html_to_text(content))
        text = "\n\n".join(parts)
        if text.strip():
            return re.sub(r"\n\s*\n", "\n\n", text).strip()
    except Exception:
        pass

    # 方式2: 当作 ZIP 直接提取 XHTML/HTML
    try:
        parts = []
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            for name in sorted(zf.namelist()):
                if name.lower().endswith((".xhtml", ".html", ".htm")):
                    content = zf.read(name).decode("utf-8", errors="replace")
                    parts.append(_html_to_text(content))
        text = "\n\n".join(parts)
        if text.strip():
            return re.sub(r"\n\s*\n", "\n\n", text).strip()
    except Exception:
        pass

    raise ValueError("无效的 EPUB 文件，无法解析")


def _extract_pdf(raw: bytes) -> str:
    from PyPDF2 import PdfReader
    try:
        reader = PdfReader(BytesIO(raw))
    except Exception:
        raise ValueError("无效的 PDF 文件")
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n\n".join(parts).strip()


def _extract_docx(raw: bytes) -> str:
    from docx import Document
    try:
        doc = Document(BytesIO(raw))
    except Exception:
        raise ValueError("无效的 DOCX 文件")
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(parts)


def get_title_from_filename(filename: str) -> str:
    name = os.path.splitext(os.path.basename(filename))[0]
    return name if name else "未命名"


def sanitize_filename(filename: str) -> str:
    """移除路径遍历字符，只保留安全字符"""
    name = os.path.basename(filename)
    safe = re.sub(r'[^\w一-鿿.\-]', '_', name)
    if not safe.strip():
        import uuid
        safe = f"{uuid.uuid4()}.txt"
    return safe
