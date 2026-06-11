import os
import re
import tempfile
import zipfile
from io import BytesIO


VALID_ENCODINGS = {"auto", "utf-8", "gbk", "gb18030"}

def extract_text(file_bytes: bytes, filename: str, encoding_hint: str = "auto", errors: str = "strict") -> str:
    """根据扩展名提取文本。encoding_hint: auto|utf-8|gbk|gb18030, errors: strict|replace|ignore"""
    ext = os.path.splitext(filename)[1].lower()

    if encoding_hint != "auto" and ext in (".txt", ".md"):
        return file_bytes.decode(encoding_hint, errors=errors)

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
    """提取 EPUB 正文，优先使用 spine+TOC 过滤非正文章节。
    针对 LOFTER 等平台导出的 EPUB 做了特殊结构适配。
    """
    try:
        from ebooklib import epub
        from bs4 import BeautifulSoup

        fd, tmp_path = tempfile.mkstemp(suffix=".epub")
        try:
            os.write(fd, raw)
            os.close(fd)
            book = epub.read_epub(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        parts: list[str] = []

        for itemref in book.spine:
            item_id = itemref[0] if isinstance(itemref, tuple) else itemref
            item = book.get_item_with_id(item_id)
            if not item:
                continue

            content = item.get_content().decode("utf-8", errors="replace")
            soup = BeautifulSoup(content, "html.parser")

            # 排除目录页 (nav/toc)
            nav = soup.find("nav", {"epub:type": "toc"}) or soup.find(attrs={"role": "doc-toc"})
            if nav:
                continue

            # LOFTER 特殊结构：提取 .content .text
            text_container = soup.select_one(".content .text")
            if text_container:
                for sel in [".tag", ".link", "#comment", "#hot", ".page", ".side", "iframe", "script", "style"]:
                    for el in text_container.select(sel):
                        el.decompose()
                text = text_container.get_text(separator="\n", strip=True)
                if text:
                    parts.append(text)
                continue

            # 通用 EPUB：优先提取 epub:type="chapter" 或 role="doc-chapter"
            chapter = soup.find(attrs={"epub:type": "chapter"}) or soup.find(attrs={"role": "doc-chapter"})
            if chapter:
                for script in chapter.find_all(["script", "style"]):
                    script.decompose()
                text = chapter.get_text(separator="\n", strip=True)
                if text:
                    parts.append(text)
                continue

            # 兜底：提取 body 正文段落
            body = soup.find("body")
            if body:
                for script in body.find_all(["script", "style", "nav"]):
                    script.decompose()
                text = body.get_text(separator="\n", strip=True)
                if text:
                    parts.append(text)

        if parts:
            text = "\n\n".join(parts)
            return re.sub(r"\n[ \t]*\n", "\n\n", text).strip()
    except Exception:
        pass

    # 方式2: 当作 ZIP 直接提取 XHTML/HTML（BS4 降级）
    try:
        from bs4 import BeautifulSoup
        parts = []
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            for name in sorted(zf.namelist()):
                if name.lower().endswith((".xhtml", ".html", ".htm")):
                    content = zf.read(name).decode("utf-8", errors="replace")
                    soup = BeautifulSoup(content, "html.parser")
                    body = soup.find("body")
                    if body:
                        for script in body.find_all(["script", "style", "nav"]):
                            script.decompose()
                        text = body.get_text(separator="\n", strip=True)
                        if text:
                            parts.append(text)
        if parts:
            text = "\n\n".join(parts)
            return re.sub(r"\n[ \t]*\n", "\n\n", text).strip()
    except Exception:
        pass

    raise ValueError("无效的 EPUB 文件，无法解析")


def extract_epub_chapters(raw: bytes) -> list:
    """从 EPUB 的 spine 直接提取章节，返回 ChapterData 列表（EPUB 信任分章）。
    如果 spine 分章失败，退回纯文本模式返回空列表。
    """
    try:
        from ebooklib import epub
        from bs4 import BeautifulSoup
        from personal_library.core.chapter_parser import ChapterData, _hash_content
        from personal_library.core.xss import sanitize_html

        fd, tmp_path = tempfile.mkstemp(suffix=".epub")
        try:
            os.write(fd, raw)
            os.close(fd)
            book = epub.read_epub(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        chapters: list[ChapterData] = []
        position = 0
        chap_idx = 1

        for itemref in book.spine:
            item_id = itemref[0] if isinstance(itemref, tuple) else itemref
            item = book.get_item_with_id(item_id)
            if not item:
                continue

            content = item.get_content().decode("utf-8", errors="replace")
            soup = BeautifulSoup(content, "html.parser")

            # 排除目录页
            nav = soup.find("nav", {"epub:type": "toc"}) or soup.find(attrs={"role": "doc-toc"})
            if nav:
                continue

            # LOFTER 特殊结构
            text_container = soup.select_one(".content .text")
            if text_container:
                for sel in [".tag", ".link", "#comment", "#hot", ".page", ".side", "iframe", "script", "style"]:
                    for el in text_container.select(sel):
                        el.decompose()
                text = text_container.get_text(separator="\n", strip=True)
            else:
                chapter = soup.find(attrs={"epub:type": "chapter"}) or soup.find(attrs={"role": "doc-chapter"})
                if chapter:
                    for script in chapter.find_all(["script", "style"]):
                        script.decompose()
                    text = chapter.get_text(separator="\n", strip=True)
                else:
                    body = soup.find("body")
                    if body:
                        for script in body.find_all(["script", "style", "nav"]):
                            script.decompose()
                        text = body.get_text(separator="\n", strip=True)
                    else:
                        text = ""

            if not text.strip():
                continue

            text = re.sub(r"\n[ \t]*\n", "\n\n", text).strip()
            text = cleanup_text(text)
            safe_text = sanitize_html(text)
            content_bytes = text.encode("utf-8")
            start_pos = position
            end_pos = position + len(content_bytes)
            position = end_pos + 1  # +1 for separator

            # 尝试从内容中提取章节标题（第一行或h1）
            title = ""
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)
            if not title:
                first_line = text.split("\n")[0].strip()
                if len(first_line) <= 80:
                    title = first_line
            if not title:
                title = f"第{chap_idx}章"

            chapters.append(ChapterData(
                chapter_number=chap_idx,
                title=title,
                content=safe_text,
                start_position=start_pos,
                end_position=end_pos,
                word_count=len(safe_text),
                content_hash=_hash_content(safe_text),
            ))
            chap_idx += 1

        return chapters
    except Exception:
        return []


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
    """从文件名提取标题，去掉常见哈希后缀和活动标签。"""
    import unicodedata
    name = os.path.splitext(os.path.basename(filename))[0]
    name = unicodedata.normalize("NFC", name)
    # 去掉末尾 _<hex> 哈希后缀
    name = re.sub(r"_[0-9a-f]{6,}$", "", name, flags=re.IGNORECASE)
    # 去掉末尾 -<数字> 编号后缀
    name = re.sub(r"-\d+$", "", name)
    # 去掉首尾空格
    name = name.strip()
    return name if name else "未命名"


def cleanup_text(text: str) -> str:
    """文本清洗：合并空行、移除装饰线、元数据行、社交标签、导航链接等。"""
    # 统一换行
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 合并连续 4+ 空行为双空行
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    # 元数据行正则（LOFTER 等平台）
    _META_PATTERNS = [
        # 作者 | 日期 | 热度 等元数据行
        re.compile(r"^\s*作者[：:]\s*.+?\|.+$", re.MULTILINE),
        # 热度/阅读/评论/推荐/喜欢 数字统计行
        re.compile(r"^\s*(热度|阅读|评论|推荐|喜欢|浏览|收藏)[：:]?\s*\d+.*$", re.MULTILINE),
        # 多字段元数据行（含多个 | 分隔）
        re.compile(r"^\s*(热度|阅读|评论|推荐|喜欢|作者|日期|时间)[：:]\s*[^|]+(?:\|[^|]+){1,}\s*$", re.MULTILINE),
        # 纯社交媒体标签行（整行都是 #标签#）
        re.compile(r"^\s*(?:#\S+#\s*)+$", re.MULTILINE),
        # 导航链接行
        re.compile(r"^\s*(下一章|上一章|目录|返回|回目录|查看全文|点击.*下一章|点击.*阅读).*$")
    ]

    lines = text.split("\n")
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append(line)
            continue

        # 保留 Markdown 表格
        if "|" in stripped and stripped[0] in "|:-":
            cleaned.append(line)
            continue

        # 移除纯装饰线：单字符重复 ≥8 次的标点
        # 必须在注释检查之前，避免 ************ 被当作 /* 注释保留
        if len(stripped) >= 8 and len(set(stripped)) == 1 and not stripped.isalnum():
            continue

        # 保留注释行（# // /* 开头）—— 排除纯重复装饰线后
        if stripped[0] in ("#", "/", "*") and len(stripped) > 1 and stripped[1] in ("#", "/", "*", " "):
            cleaned.append(line)
            continue

        # 移除元数据/标签/导航行
        skip = False
        for pat in _META_PATTERNS:
            if pat.search(line):
                skip = True
                break
        if skip:
            continue

        # 移除内联社交标签（如 正文#标签#正文 → 保留正文，移除标签）
        # 但只在 aggressive 模式下做，保守模式保留
        # 这里采用保守策略：只移除明显是元数据的标签
        cleaned.append(line)

    return "\n".join(cleaned).strip()


def sanitize_filename(filename: str) -> str:
    """移除路径遍历字符，保留安全字符（含 CJK 扩展区汉字）。"""
    import unicodedata
    import uuid

    name = os.path.basename(filename)
    name = unicodedata.normalize("NFC", name)

    def _is_safe(ch: str) -> bool:
        cp = ord(ch)
        # ASCII 字母数字下划线
        if ch.isascii():
            return ch.isalnum() or ch in "_.-"
        # CJK 统一汉字 (U+4E00 - U+9FFF)
        if 0x4E00 <= cp <= 0x9FFF:
            return True
        # CJK 扩展 A (U+3400 - U+4DBF)
        if 0x3400 <= cp <= 0x4DBF:
            return True
        # CJK 扩展 B-F (U+20000 - U+2A6DF) 及 G (U+30000 - U+3134F)
        if 0x20000 <= cp <= 0x2A6DF:
            return True
        if 0x30000 <= cp <= 0x3134F:
            return True
        # CJK 兼容汉字 / 符号标点 / 全角字符
        if 0xF900 <= cp <= 0xFAFF:
            return True
        if 0x3000 <= cp <= 0x303F:
            return True
        if 0xFF00 <= cp <= 0xFFEF:
            return True
        return False

    safe = "".join(ch if _is_safe(ch) else "_" for ch in name).strip(". ")
    if not safe:
        safe = f"{uuid.uuid4()}.txt"
    return safe
