"""
chunker.py – Markdown-aware document chunking for HTB writeups.

Takes a raw ``.md`` file path and returns a list of chunk dicts with rich
metadata extracted from document structure, headings, and content.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.config import CHUNK_TOKEN_LIMIT

# ── Constants ────────────────────────────────────────────────────────────────

CHAR_LIMIT = CHUNK_TOKEN_LIMIT * 4          # ≈ 2 400 chars (≈ 600 tokens)

KNOWN_TOOLS: set[str] = {
    "nmap", "gobuster", "ffuf", "feroxbuster",
    "bloodhound", "sharphound",
    "impacket", "secretsdump", "psexec", "wmiexec", "smbexec",
    "crackmapexec", "netexec", "cme",
    "evil-winrm", "certipy", "certify",
    "rubeus", "hashcat", "john",
    "sqlmap", "burpsuite", "chisel", "ligolo",
    "linpeas", "winpeas", "metasploit", "msfvenom",
    "smbclient", "rpcclient", "kerbrute",
}

ATTACK_PHASE_MAP: dict[str, list[str]] = {
    "recon":            ["recon", "scanning", "enumeration"],
    "foothold":         ["shell as", "foothold", "user", "initial access"],
    "lateral-movement": ["lateral", "pivot", "move"],
    "privesc":          ["root", "privilege", "escalation", "admin"],
    "persistence":      ["persistence", "beyond root"],
}

IGNORE_HEADINGS: set[str] = {
    "box info",
    "box information",
    "machine info",
    "filtering",
    "alternative methods for finding ipv6",
    "from arp",
}

_IMAGE_RE = re.compile(r"!\[.*?\]\(.*?\)")
_CVE_RE   = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _machine_name(stem: str) -> str:
    """Derive display name from filename stem.

    >>> _machine_name("htb-certified")
    'Certified'
    >>> _machine_name("htb-la-casa-de-papel")
    'La Casa De Papel'
    """
    name = stem
    if name.lower().startswith("htb-"):
        name = name[4:]
    return name.replace("-", " ").title()


def _detect_os(text: str) -> str:
    """Search for 'Windows' or 'Linux' in *text*."""
    low = text.lower()
    if "windows" in low:
        return "windows"
    if "linux" in low:
        return "linux"
    return "unknown"


def _detect_difficulty(text: str) -> str:
    """Match standalone Easy / Medium / Hard / Insane."""
    low = text.lower()
    for diff in ("insane", "hard", "medium", "easy"):
        if re.search(rf"\b{diff}\b", low):
            return diff
    return "unknown"


def _attack_phase(h2: str) -> str:
    """Classify the attack phase from an ## heading."""
    low = h2.lower()
    if any(kw in low for kw in ["root", "admin", "administrator", "system", "privilege", "escalation", "privesc"]):
        return "privesc"
    if any(kw in low for kw in ["recon", "scanning", "enumeration"]):
        return "recon"
    if any(kw in low for kw in ["shell as", "foothold", "user", "initial access", "compromise"]):
        return "foothold"
    if any(kw in low for kw in ["lateral", "pivot", "move"]):
        return "lateral-movement"
    if any(kw in low for kw in ["persistence", "beyond root"]):
        return "persistence"
    return "unknown"


_TOOL_PATTERNS: dict[str, re.Pattern] = {
    tool: re.compile(rf"\b{re.escape(tool)}\b", re.IGNORECASE)
    for tool in KNOWN_TOOLS
}


def _find_tools(text: str) -> list[str]:
    """Return sorted list of known tools mentioned in text using exact word boundaries."""
    return sorted(tool for tool, pat in _TOOL_PATTERNS.items() if pat.search(text))


def _has_code(text: str) -> bool:
    """True if *text* contains a fenced or indented code block."""
    return "```" in text or bool(re.search(r"^    \S", text, re.MULTILINE))


def _extract_cves(text: str) -> list[str]:
    """Return sorted, de-duplicated CVE identifiers."""
    return sorted(set(_CVE_RE.findall(text)))


def _clean(text: str) -> str:
    """Remove image markdown lines (``![alt](url)``)."""
    return _IMAGE_RE.sub("", text).strip()


def _breadcrumb(h2: str, h3: str = "", h4: str = "") -> str:
    """Build 'h2 > h3 > h4' breadcrumb string."""
    parts = [p.strip() for p in (h2, h3, h4) if p and p.strip()]
    return " > ".join(parts)


def _split_into_paragraphs(text: str, max_chars: int = CHAR_LIMIT) -> list[str]:
    """Split oversized text into chunks under max_chars while ensuring code blocks are balanced."""
    budget = max_chars - 80  # Reserve buffer for fence closing/re-opening
    paragraphs = text.split("\n\n")
    refined: list[str] = []
    for p in paragraphs:
        if len(p) > budget:
            lines = p.split("\n")
            cur_lines: list[str] = []
            cur_l = 0
            for line in lines:
                if len(line) > budget:
                    if cur_lines:
                        refined.append("\n".join(cur_lines))
                        cur_lines = []
                        cur_l = 0
                    for i in range(0, len(line), budget):
                        refined.append(line[i : i + budget])
                    continue
                if cur_l + len(line) + 1 > budget and cur_lines:
                    refined.append("\n".join(cur_lines))
                    cur_lines = [line]
                    cur_l = len(line)
                else:
                    cur_lines.append(line)
                    cur_l += len(line) + 1
            if cur_lines:
                refined.append("\n".join(cur_lines))
        else:
            refined.append(p)

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0
    in_code_block = False
    current_lang = ""

    for p in refined:
        p_str = p.strip()
        if not p_str:
            continue

        if current_len + len(p_str) + 2 > budget and current_chunk:
            chunk_body = "\n\n".join(current_chunk)
            # If splitting inside a code block, close it cleanly
            if in_code_block:
                chunk_body += "\n```"
            chunks.append(chunk_body)

            # Re-open the code block at the beginning of the next chunk
            if in_code_block:
                current_chunk = [f"```{current_lang}\n{p_str}"]
            else:
                current_chunk = [p_str]
            current_len = len(current_chunk[0])
        else:
            current_chunk.append(p_str)
            current_len += len(p_str) + 2

        # Track opening/closing of code fences and capture code language
        for line in p_str.split("\n"):
            line_str = line.strip()
            if line_str.startswith("```"):
                if in_code_block:
                    in_code_block = False
                    current_lang = ""
                else:
                    in_code_block = True
                    current_lang = line_str[3:].strip()

    if current_chunk:
        chunk_body = "\n\n".join(current_chunk)
        if in_code_block:
            chunk_body += "\n```"
        chunks.append(chunk_body)

    return chunks if chunks else [text]




# ── Code-block–aware heading splitter ────────────────────────────────────────

def _code_block_ranges(text: str) -> list[tuple[int, int]]:
    """Return ``(start, end)`` char-offset pairs for every fenced code block."""
    return [(m.start(), m.end()) for m in re.finditer(r"```[\s\S]*?```", text)]


def _split_at_level(text: str, level: int) -> list[tuple[str, str]]:
    """Split *text* by headings at exactly *level* (ignoring code blocks).

    Returns ``[(heading, body), ...]``.  The first entry may have
    ``heading=""`` for content that precedes the first heading.
    """
    prefix = "#" * level
    pattern = re.compile(
        rf"^{re.escape(prefix)}(?!#)\s+(.*)", re.MULTILINE,
    )
    code_ranges = _code_block_ranges(text)

    def _in_code(pos: int) -> bool:
        return any(s <= pos < e for s, e in code_ranges)

    hits = [
        (m.start(), m.group(1).strip())
        for m in pattern.finditer(text)
        if not _in_code(m.start())
    ]

    if not hits:
        return [("", text)]

    parts: list[tuple[str, str]] = []

    # Content before the first heading at this level
    pre = text[: hits[0][0]].strip()
    if pre:
        parts.append(("", pre))

    for i, (pos, heading) in enumerate(hits):
        end = hits[i + 1][0] if i + 1 < len(hits) else len(text)
        nl = text.find("\n", pos)
        body_start = (nl + 1) if nl != -1 and nl < end else end
        body = text[body_start:end].strip()
        parts.append((heading, body))

    return parts


# ── Box Info extraction ──────────────────────────────────────────────────────

def _parse_box_info(intro: str) -> tuple[str, str, str]:
    """Find the Box Info table in *intro*, extract OS & difficulty.

    Returns ``(os, difficulty, intro_without_box_info_table)``.
    """
    lines = intro.split("\n")
    table_idx: set[int] = set()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("|"):
            table_idx.add(i)
        elif re.fullmatch(r"[-|:\s]+", stripped) and "|" in stripped:
            table_idx.add(i)

    os_val  = "unknown"
    diff_val = "unknown"

    if table_idx:
        table_text = "\n".join(lines[i] for i in sorted(table_idx))
        os_val  = _detect_os(table_text)
        diff_val = _detect_difficulty(table_text)
        # Strip the entire table block
        kept = [l for i, l in enumerate(lines) if i not in table_idx]
        return os_val, diff_val, "\n".join(kept).strip()

    # Fallback: scan first few lines for ``OS:`` / ``Difficulty:`` labels
    for line in lines[:15]:
        low = line.lower()
        if os_val == "unknown" and ("os" in low or "operating" in low):
            os_val = _detect_os(line)
        if diff_val == "unknown" and ("difficult" in low or "level" in low):
            diff_val = _detect_difficulty(line)

    return os_val, diff_val, intro


# ── Public API ───────────────────────────────────────────────────────────────

def chunk_file(md_path: str) -> list[dict[str, Any]]:
    """Parse a raw HTB writeup ``.md`` file and return a list of chunk dicts.

    Parameters
    ----------
    md_path : str
        Absolute path to a ``.md`` file.

    Returns
    -------
    list[dict]
        Each dict has the keys: ``text``, ``source``, ``machine_name``,
        ``os``, ``difficulty``, ``h2``, ``h3``, ``breadcrumb``,
        ``chunk_type``, ``has_cve``, ``cve_ids``, ``tools_mentioned``,
        ``has_code``, ``attack_phase``, ``stub_file``.
    """
    path = Path(md_path)
    stem   = path.stem
    source = stem
    name   = _machine_name(stem)

    raw = path.read_text(encoding="utf-8", errors="ignore")

    # FIX: Normalize stuck headings (e.g. "Creator ## Recon" -> "Creator\n\n## Recon")
    raw = re.sub(r'([^\n#\r])[ \t]*(#{2,4}[ \t]+[A-Za-z0-9])', r'\1\n\n\2', raw)

    # ── Rule 6: stub detection (raw word count) ──────────────────────────
    is_stub = len(raw.split()) < 500

    # ── Rule 8: remove image lines ───────────────────────────────────────
    cleaned = _clean(raw)

    # ── Split at ## level ────────────────────────────────────────────────
    h2_parts = _split_at_level(cleaned, 2)

    intro_raw: str = ""
    h2_sections: list[tuple[str, str]] = []

    if h2_parts and h2_parts[0][0] == "":
        intro_raw   = h2_parts[0][1]
        h2_sections = h2_parts[1:]
    else:
        h2_sections = h2_parts

    # ── Rule 1: parse Box Info → extract os, difficulty → skip block ─────
    detected_os, difficulty, intro_clean = _parse_box_info(intro_raw)
    if detected_os == "unknown":
        detected_os = _detect_os(raw[:4000])
    if difficulty == "unknown":
        difficulty = _detect_difficulty(raw[:4000])


    # Strip ``# Title`` line from intro so only prose remains
    intro_clean = re.sub(
        r"^#(?!#)\s+.*$", "", intro_clean, count=1, flags=re.MULTILINE,
    ).strip()

    # ── Rule 5: check whether file has any ### headings ──────────────────
    has_h3 = any(
        len(_split_at_level(body, 3)) > 1 for _, body in h2_sections
    )

    # ── Chunk emitter ────────────────────────────────────────────────────
    chunks: list[dict[str, Any]] = []

    def _emit(text: str, h2: str, h3: str = "", h4: str = "", chunk_type: str = "text") -> None:
        """Build a chunk dict with rich semantic context."""
        text = text.strip()
        if len(text) < 80:
            return

        if h2.lower().strip() in IGNORE_HEADINGS or h3.lower().strip() in IGNORE_HEADINGS or (h4 and h4.lower().strip() in IGNORE_HEADINGS):
            return

        # Recursive split if single chunk still exceeds CHAR_LIMIT
        if len(text) > CHAR_LIMIT:
            sub_parts = _split_into_paragraphs(text, CHAR_LIMIT)
            if len(sub_parts) > 1 and all(len(s) < len(text) for s in sub_parts):
                for sub in sub_parts:
                    _emit(sub, h2, h3, h4, chunk_type)
                return

        bc       = _breadcrumb(h2, h3, h4)
        phase    = _attack_phase(h2)
        # Rich Context Prefix for high-accuracy BM25 & dense vector matching
        prefixed = f"[Machine: {name} | OS: {detected_os.capitalize()} | Phase: {phase.capitalize()} | Path: {bc}]\n\n{text}"
        cves     = _extract_cves(text)

        chunks.append({
            "text":            prefixed,
            "source":          source,
            "machine_name":    name,
            "os":              detected_os,
            "difficulty":      difficulty,
            "h2":              h2,
            "h3":              h3,
            "h4":              h4,
            "breadcrumb":      bc,
            "chunk_type":      chunk_type,
            "has_cve":         bool(cves),
            "cve_ids":         cves,
            "tools_mentioned": _find_tools(text),
            "has_code":        _has_code(text),
            "attack_phase":    phase,
            "stub_file":       is_stub,
        })

    # ── Rule 2: intro paragraph → one "summary" chunk ───────────────────
    if intro_clean:
        _emit(intro_clean, name, "", "", "summary")

    # ── Rules 3-5: section chunking ──────────────────────────────────────
    if has_h3:
        # Rule 3: primary split by ### within each ## section
        for h2_heading, h2_body in h2_sections:
            for h3_heading, h3_body in _split_at_level(h2_body, 3):
                if not h3_body.strip():
                    continue
                # Rule 4: sub-split by #### if > CHAR_LIMIT
                if len(h3_body) > CHAR_LIMIT:
                    for h4_heading, h4_body in _split_at_level(h3_body, 4):
                        _emit(h4_body, h2_heading, h3_heading, h4_heading)
                else:
                    _emit(h3_body, h2_heading, h3_heading)
    else:
        # Rule 5: flat / old file — split by ## only
        for h2_heading, h2_body in h2_sections:
            _emit(h2_body, h2_heading, "")

    # ── Edge case: no sections produced at all ───────────────────────────
    if not chunks and cleaned:
        _emit(cleaned, name, "", "", "summary")

    return chunks
