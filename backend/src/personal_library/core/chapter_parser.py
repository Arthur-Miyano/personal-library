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
    suffix: str = ""
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

# 行首装饰字符（要去掉才能匹配）
_STRIP_RE = re.compile(r"^[\s\-=【】\[\]()（）#*~]+|[\s\-=【】\[\]()（）#*~]+$")

# 核心章节匹配模式（按优先级排序）
_CHAPTER_PATTERNS: list[tuple[re.Pattern, int | None, bool]] = [
    # (regex, fixed_chapter_number, is_prologue)
    # 中文数字章：第一章、第1章
    (re.compile(r"第([零一二三四五六七八九十百千壹贰叁肆伍陆柒捌玖拾佰仟\d]+)[章回篇卷部]"
                 r"(?![零一二三四五六七八九十百千壹贰叁肆伍陆柒捌玖拾佰仟\d一-鿿])"), None, False),
    # 英文章节：Chapter 1 / CHAPTER ONE
    (re.compile(r"[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s+(\d+|[Oo][Nn][Ee]|[Tt][Ww][Oo]|[Tt][Hh][Rr][Ee][Ee]|"
                 r"[Ff][Oo][Uu][Rr]|[Ff][Ii][Vv][Ee]|[Ss][Ii][Xx]|[Ss][Ee][Vv][Ee][Nn]|[Ee][Ii][Gg][Hh][Tt]|"
                 r"[Nn][Ii][Nn][Ee]|[Tt][Ee][Nn])\b"), None, False),
    # 数字编号章节：1. 标题 / 1、标题
    (re.compile(r"^(\d{1,3})[\.、]\s+\S+$"), None, False),
    # 序言类
    (re.compile(r"^(?:楔子|引子|序章|前言|序言|自序|他序|写在前面)$"), 0, True),
    # 尾声类
    (re.compile(r"^(?:尾声|后记|番外|附录|结语)$"), -1, False),
]

# 序章/尾声类标题（用于第二遍匹配，给它们分配章节号）
_PROLOGUE_TITLES = {"楔子", "引子", "序章", "前言", "序言", "自序", "他序", "写在前面"}
_EPILOGUE_TITLES = {"尾声", "后记", "番外", "附录", "结语"}


def _parse_cn_num(s: str) -> int:
    """将中文数字字符串转为整数，如 '十二'→12, '一百零一'→101"""
    if s.isdigit():
        return int(s)

    result = 0
    section = 0

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


_EN_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


def _parse_en_num(s: str) -> int:
    """将英文数字转为整数。"""
    s = s.lower()
    if s.isdigit():
        return int(s)
    return _EN_NUM.get(s, 0)


def _hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _find_nearest_break(lines: list[str], idx: int, direction: int = -1) -> int:
    """从 idx 向 direction 方向寻找最近的空行。找不到则返回 idx。
    direction=-1 向上找，direction=1 向下找。
    """
    i = idx
    while 0 <= i < len(lines):
        if not lines[i].strip():
            return i
        i += direction
    return idx


def _match_chapter(line: str) -> tuple[int | None, str, bool] | None:
    """匹配单行章节标题。返回 (chapter_number, raw_title, is_prologue) 或 None。
    chapter_number 为 None 表示需要从标题中提取数字。
    """
    stripped = _STRIP_RE.sub("", line.strip())
    if not stripped:
        return None

    for pat, fixed_cn, is_prologue in _CHAPTER_PATTERNS:
        m = pat.match(stripped)
        if m:
            title = line.strip()
            if fixed_cn is not None:
                return (fixed_cn, title, is_prologue)
            # 从捕获组提取数字
            num_str = m.group(1)
            cn = _parse_cn_num(num_str)
            if cn == 0:
                cn = _parse_en_num(num_str)
            if cn > 0:
                return (cn, title, is_prologue)
            # 对于 "第零章" 等，视为序言
            return (0, title, True)

    return None


def parse_chapters(text: str) -> list[ChapterData]:
    """输入全文文本，返回章节列表。空文本返回空列表。
    支持：第X章/回/篇/卷/部、Chapter X、数字编号、楔子/前言/尾声/番外等。
    使用寻近断行：章节边界优先落在最近的空行处。
    """
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
    raw_matches: list[tuple[int, int | None, str, bool]] = []  # (line_index, chapter_number, title, is_prologue)
    for i, line in enumerate(lines):
        result = _match_chapter(line)
        if result:
            cn, title, is_prologue = result
            raw_matches.append((i, cn, title, is_prologue))

    # 第二遍：分配章节号给序言/尾声类
    matches: list[tuple[int, int, str, bool]] = []
    prologue_count = 0
    epilogue_count = 0
    max_chapter = 0

    # 先计算最大正文章节号
    for _, cn, _, _ in raw_matches:
        if cn is not None and cn > 0:
            max_chapter = max(max_chapter, cn)

    for line_idx, cn, title, is_prologue in raw_matches:
        if cn == 0:
            # 序言类：分配负号前缀（如 0, -1, -2...）
            prologue_count += 1
            matches.append((line_idx, -(prologue_count - 1), title, True))
        elif cn == -1:
            # 尾声类：分配 max+1, max+2...
            epilogue_count += 1
            matches.append((line_idx, max_chapter + epilogue_count, title, False))
        else:
            matches.append((line_idx, cn, title, is_prologue))

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

    # 寻近断行：调整章节边界到最近的空行
    # 每个章节的起始 = max(上一个标题结束后的第一个非空行, 当前标题后的第一个空行+1)
    # 简化：章节内容从当前标题行之后开始，但如果有空行则对齐到空行后
    boundaries: list[int] = []  # 每个章节内容起始行
    for idx, (line_idx, _, _, _) in enumerate(matches):
        # 默认从标题下一行开始
        start = line_idx + 1
        # 向下找第一个空行，如果空行在合理范围内（<=3行），则从空行后开始
        blank = _find_nearest_break(lines, start, direction=1)
        if blank != start and blank - start <= 3:
            start = blank + 1
        # 但不要超过下一个标题
        if idx + 1 < len(matches) and start >= matches[idx + 1][0]:
            start = line_idx + 1
        boundaries.append(start)

    chapters: list[ChapterData] = []
    seen_numbers: set[int] = set()
    suffix_counter: dict[int, int] = {}

    # 序言：第一个标题前的非空内容
    first_match_line = matches[0][0]
    prologue_start = 0
    # 向上寻近：找到第一个标题前的最近空行作为序言边界
    prologue_blank = _find_nearest_break(lines, first_match_line, direction=-1)
    if prologue_blank != first_match_line and first_match_line - prologue_blank <= 2:
        prologue_start = prologue_blank + 1
    prologue_lines = lines[prologue_start:first_match_line]
    prologue_text = sanitize_html("\n".join(prologue_lines).strip())
    if prologue_text:
        chapters.append(ChapterData(
            chapter_number=0,
            title="序言",
            content=prologue_text,
            start_position=line_offsets[prologue_start] if prologue_start < len(lines) else 0,
            end_position=line_offsets[first_match_line],
            word_count=len(prologue_text),
            content_hash=_hash_content(prologue_text),
            is_prologue=True,
        ))

    # 正则章节
    for idx, (line_idx, cn, raw_line, is_prologue) in enumerate(matches):
        start_line = boundaries[idx]
        end_line = matches[idx + 1][0] if idx + 1 < len(matches) else len(lines)
        # 如果 start 已经超过了 end（罕见情况），回退到标题下一行
        if start_line >= end_line:
            start_line = line_idx + 1
        if start_line >= end_line:
            start_line = end_line

        content_lines = lines[start_line:end_line]
        content = sanitize_html("\n".join(content_lines).strip())
        if not content:
            content = "\n"

        content_hash = _hash_content(content)

        start_pos = line_offsets[start_line] if start_line < len(line_offsets) else len(encoded)
        end_pos = line_offsets[end_line] if end_line < len(line_offsets) else len(encoded)
        if end_pos <= start_pos:
            end_pos = start_pos + len(content.encode("utf-8"))

        if cn in seen_numbers:
            # 同号冲突：检查内容是否与已有同号章节相同
            existing = next(
                (c for c in chapters if c.chapter_number == cn and not c.is_prologue),
                None,
            )
            if existing and existing.content_hash == content_hash:
                existing.content += "\n\n---\n\n" + content
                existing.end_position = end_pos
                existing.word_count = len(existing.content)
                existing.needs_review = True
                continue

            # 内容不同 → 后缀分支
            if cn not in suffix_counter:
                suffix_counter[cn] = 1
                for ch in chapters:
                    if ch.chapter_number == cn and not ch.is_prologue and ch.suffix == "":
                        ch.suffix = "A"
                        ch.needs_review = True
            else:
                suffix_counter[cn] += 1

            suffix = chr(64 + suffix_counter[cn])
            chapters.append(ChapterData(
                chapter_number=cn,
                suffix=suffix,
                title=raw_line,
                content=content,
                start_position=start_pos,
                end_position=end_pos,
                word_count=len(content),
                content_hash=content_hash,
                needs_review=True,
            ))
        else:
            seen_numbers.add(cn)
            chapters.append(ChapterData(
                chapter_number=cn,
                title=raw_line,
                content=content,
                start_position=start_pos,
                end_position=end_pos,
                word_count=len(content),
                content_hash=content_hash,
                is_prologue=is_prologue,
            ))

    # 按章节号排序（序言在前，正文章节在中，尾声在后）
    chapters.sort(key=lambda c: c.chapter_number)
    return chapters
