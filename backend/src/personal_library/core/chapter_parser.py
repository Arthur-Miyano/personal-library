import hashlib
import re
from dataclasses import dataclass

from personal_library.core.xss import sanitize_html


@dataclass
class ChapterData:
    chapter_number: int
    title: str
    content: str
    start_position: int
    end_position: int
    word_count: int
    content_hash: str
    is_prologue: bool = False
    needs_review: bool = False


# 中文数字 → 数值映射
_CN_NUM = {
    "零": 0, "一": 1, "二": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
    "两": 2,
    "十": 10, "百": 100, "千": 1000,
    "壹": 1, "贰": 2, "叁": 3, "肆": 4,
    "伍": 5, "陆": 6, "柒": 7, "捌": 8, "玖": 9,
    "拾": 10, "佰": 100, "仟": 1000,
}

# 匹配：第 + 中文数字/阿拉伯数字 + 章
_CHAPTER_PATTERN = re.compile(
    r"第([零一二三四五六七八九十百千壹贰叁肆伍陆柒捌玖拾佰仟\d]+)章"
    r"(?![零一二三四五六七八九十百千壹贰叁肆伍陆柒捌玖拾佰仟\d一-鿿])"
)

# 行首装饰字符（要去掉才能匹配）
_STRIP_RE = re.compile(r"^[\s\-=【】\[\]()（）#*~]+|[\s\-=【】\[\]()（）#*~]+$")


def _parse_cn_num(s: str) -> int:
    """将中文数字字符串转为整数，如 '十二'→12, '一百零一'→101"""
    if s.isdigit():
        return int(s)

    result = 0
    section = 0  # 当前节（万以下处理千/百/十）

    for ch in s:
        val = _CN_NUM.get(ch)
        if val is None:
            continue
        if val >= 10:
            section = max(section, 1) * val
            if val >= 100:
                result += section
                section = 0
        else:
            section += val

    result += section
    return result


def _hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_chapters(text: str) -> list[ChapterData]:
    """输入全文文本，返回章节列表。空文本返回空列表。"""
    if not text or not text.strip():
        return []

    lines = text.split("\n")
    encoded = text.encode("utf-8")
    line_offsets: list[int] = []
    offset = 0
    for line in lines:
        line_offsets.append(offset)
        offset += len(line.encode("utf-8")) + 1  # +1 for \n

    # 第一遍：找到所有章节标题行
    matches: list[tuple[int, int, str]] = []  # (line_index, chapter_number, raw_line)
    for i, line in enumerate(lines):
        stripped = _STRIP_RE.sub("", line.strip())
        m = _CHAPTER_PATTERN.match(stripped)
        if m:
            cn = _parse_cn_num(m.group(1))
            if cn > 0:
                matches.append((i, cn, line.strip()))

    if not matches:
        # 无章节标题 → 整本书作为单章
        content = sanitize_html(text.strip())
        return [ChapterData(
            chapter_number=1,
            title="全文",
            content=content,
            start_position=0,
            end_position=len(encoded),
            word_count=len(content),
            content_hash=_hash_content(content),
        )]

    chapters: list[ChapterData] = []
    seen_numbers: set[int] = set()

    # 序言：第一个标题前的非空内容
    first_match_line = matches[0][0]
    prologue_lines = lines[:first_match_line]
    prologue_text = sanitize_html("\n".join(prologue_lines).strip())
    if prologue_text:
        chapters.append(ChapterData(
            chapter_number=1,
            title="序言",
            content=prologue_text,
            start_position=0,
            end_position=line_offsets[first_match_line],
            word_count=len(prologue_text),
            content_hash=_hash_content(prologue_text),
            is_prologue=True,
        ))

    # 正则章节
    for idx, (line_idx, cn, raw_line) in enumerate(matches):
        needs_review = cn in seen_numbers
        seen_numbers.add(cn)

        # 确定章节内容的起止行
        start_line = line_idx + 1
        end_line = matches[idx + 1][0] if idx + 1 < len(matches) else len(lines)

        content_lines = lines[start_line:end_line]
        content = sanitize_html("\n".join(content_lines).strip())
        if not content:
            content = "\n"  # 空章节给占位符，避免位置约束冲突

        start_pos = line_offsets[start_line] if start_line < len(lines) else len(encoded)
        end_pos = line_offsets[end_line] if end_line < len(lines) else len(encoded)
        if end_pos <= start_pos:
            end_pos = start_pos + len(content.encode("utf-8"))

        chapters.append(ChapterData(
            chapter_number=cn,
            title=raw_line,
            content=content,
            start_position=start_pos,
            end_position=end_pos,
            word_count=len(content),
            content_hash=_hash_content(content),
            needs_review=needs_review,
        ))

    # 如果有序言，给后续章节编号 +1 偏移（由于序言占了 1）
    # 实际上用户可能希望序言=0，但 plan 说用 is_prologue 标记
    # 这里序言 chapter_number=1 且 is_prologue=True，后续从 1 开始会有冲突
    # 修正：如果有序言，序言 chapter_number=0，后续从 1 开始
    if chapters and chapters[0].is_prologue:
        chapters[0].chapter_number = 0

    return chapters
