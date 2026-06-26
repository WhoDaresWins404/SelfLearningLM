import json
import re


# Language groups for syntax-aware line break restoration
_LANG_C_LIKE = {"c", "cpp", "c++", "cxx", "h", "hpp", "java", "js", "javascript", "ts", "typescript",
                 "cs", "csharp", "go", "rust", "rs", "swift", "kt", "kotlin", "dart", "scala", "php"}

_LANG_PYTHON = {"python", "py", "python3", "jython"}

_LANG_SHELL = {"bash", "sh", "shell", "shellscript", "zsh", "fish", "powershell", "ps1", "psm1", "psd1"}

_LANG_SQL = {"sql", "mysql", "postgresql", "pgsql", "sqlite", "tsql", "plsql"}


def _detect_lang_group(lang: str) -> str:
    lang = lang.strip().lower()
    if lang in _LANG_PYTHON:
        return "python"
    if lang in _LANG_SHELL:
        return "shell"
    if lang in _LANG_SQL:
        return "sql"
    if lang in _LANG_C_LIKE:
        return "c_like"
    return "unknown"


def reconstruct_code_block(code_block: str) -> str:
    """Reconstruct a tokenized/fragmented code block by joining tokens,
    fixing punctuation spacing, and restoring language-appropriate line breaks."""

    match = re.match(r'(```(\w*)\n)(.*?)(```)', code_block, flags=re.DOTALL)
    if not match:
        return code_block

    prefix = match.group(1)
    lang = match.group(2)
    code = match.group(3)
    suffix = match.group(4)

    # 1. Split into lines, strip, filter empty
    lines = [l.strip() for l in code.split("\n") if l.strip()]
    if not lines:
        return code_block

    # 2. Join into a single space-separated string
    code = " ".join(lines)

    # 3. Fix spacing around punctuation
    code = re.sub(r"\s+([\(\[\{,;\)\]])", r"\1", code)
    code = re.sub(r"([\(\[])\s+", r"\1", code)
    code = re.sub(r"(\w)\s+\*", r"\1*", code)
    code = re.sub(r"\*\s+(\w)", r"*\1", code)
    code = re.sub(r"\s+([.·])\s+", r"\1", code)
    code = re.sub(r"\s*->\s*", "->", code)
    code = re.sub(r"\s*::\s*", "::", code)

    # 4. Restore line breaks based on language
    group = _detect_lang_group(lang)
    if group == "python":
        code = re.sub(r"(:\s*)$", r":\n", code, flags=re.MULTILINE)
        code = re.sub(r"(:\s+)(?=\w)", r":\n", code)
    elif group == "shell":
        code = re.sub(r"(\\)\s*", r"\\\n", code)
        code = re.sub(r"(;)\s*", r";\n", code)
        code = re.sub(r"(\|)\s*", r"|\n", code)
    elif group == "sql":
        code = re.sub(r"(;)\s*", r";\n", code)
        for kw in ["SELECT", "FROM", "WHERE", "AND", "OR", "JOIN", "LEFT JOIN", "RIGHT JOIN",
                    "INNER JOIN", "OUTER JOIN", "GROUP BY", "ORDER BY", "HAVING", "LIMIT",
                    "INSERT INTO", "VALUES", "UPDATE", "SET", "DELETE FROM", "CREATE TABLE",
                    "ALTER TABLE", "DROP TABLE", "CREATE INDEX", "ON", "AS"]:
            code = re.sub(rf"(?<=\s)({re.escape(kw)})\s", lambda m: f"\n{m.group(1)} ", code, flags=re.IGNORECASE)
    else:
        code = re.sub(r"([;{}])\s*", r"\1\n", code)
        code = re.sub(r"(#\w+.*?)\s+(?=[a-zA-Z_#])", r"\1\n", code)
        code = re.sub(r"(#\s*include\s*<\s*[^>]+\s*>)\s*", r"\1\n", code)
        code = re.sub(r"(#\s*include\s*\"\s*[^\"]+\s*\")\s*", r"\1\n", code)

    # 5. Collapse multiple newlines
    code = re.sub(r"\n{3,}", "\n\n", code)

    return f"{prefix}{code.strip()}\n{suffix}"


def clean_code_text(text: str) -> str:
    """Clean text that may contain code fences, applying reconstruction to code blocks."""
    parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
    cleaned = []
    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            cleaned.append(reconstruct_code_block(part))
        else:
            cleaned.append(part)
    return "".join(cleaned)


def clean_prose(text: str) -> str:
    """Fix glued words in prose text."""
    if not text:
        return text
    text = re.sub(r'([\)\]\}])([a-z])', r'\1 \2', text)
    text = re.sub(r'([a-z])([\[\(\{])', r'\1 \2', text)
    text = re.sub(r'(\b\w+)(and|or|of|in|to|for|with|the|is|as|at|by|on|a)(\w+\b)',
                  lambda m: m.group(1) + m.group(2) + ' ' + m.group(3)
                  if m.group(2) in ('and', 'or', 'of', 'in', 'to', 'for', 'with', 'the', 'is', 'as', 'at', 'by', 'on', 'a')
                  and len(m.group(1)) > 1 and len(m.group(3)) > 1 else m.group(0), text)
    text = re.sub(r'([.,!?;:])([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    return text


def clean_content(text: str) -> str:
    """Clean a string that may contain mixed prose and ```code blocks```."""
    parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
    cleaned = []
    for part in parts:
        if part.startswith('```') and part.endswith('```'):
            cleaned.append(reconstruct_code_block(part))
        else:
            cleaned.append(clean_prose(part))
    return "".join(cleaned)


def clean_sections(sections: list[dict]) -> list[dict]:
    """Clean all paragraph text within sections."""
    for sec in sections:
        cleaned_paras = []
        for p in sec.get("paragraphs", []):
            if p.startswith("> ") or p.startswith("- "):
                cleaned_paras.append(p)
            else:
                cleaned_paras.append(clean_content(p))
        sec["paragraphs"] = cleaned_paras
    return sections


def clean_jsonl_file(input_path: str, output_path: str) -> int:
    """Standalone: read a JSONL file, clean all content fields, write output."""
    count = 0
    with open(input_path, "r", encoding="utf-8") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            for key in ("content", "instruction", "response"):
                val = record.get(key)
                if isinstance(val, str):
                    record[key] = clean_content(val)
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count
