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
    match = re.match(r'(```(\w*)\n)(.*?)(```)', code_block, flags=re.DOTALL)
    if not match:
        return code_block

    prefix = match.group(1)
    lang = match.group(2)
    code = match.group(3)
    suffix = match.group(4)

    lines = [l.strip() for l in code.split("\n") if l.strip()]
    if not lines:
        return code_block

    code = " ".join(lines)

    code = re.sub(r"\s+([\(\[\{,;\)\]])", r"\1", code)
    code = re.sub(r"([\(\[])\s+", r"\1", code)
    code = re.sub(r"(\w)\s+\*", r"\1*", code)
    code = re.sub(r"\*\s+(\w)", r"*\1", code)
    code = re.sub(r"\s+([.·])\s+", r"\1", code)
    code = re.sub(r"\s*->\s*", "->", code)
    code = re.sub(r"\s*::\s*", "::", code)

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

    code = re.sub(r"\n{3,}", "\n\n", code)

    return f"{prefix}{code.strip()}\n{suffix}"


def fix_sentence_boundaries(text: str) -> str:
    """Rejoin sentences broken across line boundaries by extraction."""
    if not text:
        return text
    parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
    fixed = []
    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            fixed.append(part)
        else:
            result = part
            result = re.sub(r'(\b(?:e|g|i|ie|vs|etc|al|approx|dept|est|govt|incl|mt|no|st|vs)\.)\n\s*([a-z])', r'\1 \2', result)
            result = re.sub(r'(\b[A-Z][a-z]{1,3}\.)\n\s*([a-z])', r'\1 \2', result)
            result = re.sub(r'([.!?])\n\s*\n', r'\1\n\n', result)
            result = re.sub(r'([a-z,;])\n\s*([a-z])', r'\1 \2', result)
            result = re.sub(r'(\w)\n\s*(\w)', lambda m: m.group(1) + ' ' + m.group(2) if m.group(2)[0].islower() else m.group(0), result)
            fixed.append(result)
    return "".join(fixed)


def clean_prose(text: str) -> str:
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
    parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
    cleaned = []
    for part in parts:
        if part.startswith('```') and part.endswith('```'):
            cleaned.append(reconstruct_code_block(part))
        else:
            cleaned.append(clean_prose(part))
    return "".join(cleaned)


def clean_sections(sections: list[dict]) -> list[dict]:
    for sec in sections:
        cleaned_paras = []
        for p in sec.get("paragraphs", []):
            if p.startswith("> ") or p.startswith("- "):
                cleaned_paras.append(p)
            else:
                cleaned_paras.append(clean_content(p))
        sec["paragraphs"] = cleaned_paras
    return sections


# --- Phase 2.3: Format-specific refiners ---

def refine_instruction_response(lines: list[dict]) -> list[dict]:
    filtered = []
    for pair in lines:
        inst = pair.get("instruction", "").strip()
        resp = pair.get("response", "").strip()
        if not inst or not resp:
            continue
        if len(resp.split()) < 5:
            continue
        if inst == resp:
            continue
        filtered.append({"instruction": inst, "response": resp})
    return filtered


def refine_code_explanation(lines: list[dict]) -> list[dict]:
    filtered = []
    for pair in lines:
        inst = pair.get("instruction", "").strip()
        resp = pair.get("response", "").strip()
        if not inst or not resp:
            continue
        if len(resp.split()) < 2 and len(inst.split()) < 2:
            continue
        if "```" not in resp and "```" not in inst:
            continue
        filtered.append({"instruction": inst, "response": resp})
    return filtered


def refine_qa(lines: list[dict]) -> list[dict]:
    filtered = []
    for pair in lines:
        question = pair.get("instruction", "").strip()
        answer = pair.get("response", "").strip()
        if not question or not answer:
            continue
        if not question.endswith("?"):
            continue
        if len(answer.split()) < 3:
            continue
        if len(question) < 5:
            continue
        filtered.append({"instruction": question, "response": answer})
    return filtered


FORMAT_REFINERS = {
    "instruction_response": refine_instruction_response,
    "code_explanation": refine_code_explanation,
    "qa": refine_qa,
}


def refine_formatted_content(content: str, fmt: str) -> str:
    refiner = FORMAT_REFINERS.get(fmt)
    if not refiner:
        return content
    lines = []
    for raw_line in content.strip().split("\n"):
        if not raw_line.strip():
            continue
        try:
            obj = json.loads(raw_line)
            if isinstance(obj, dict) and "instruction" in obj:
                lines.append(obj)
        except json.JSONDecodeError:
            pass
    if not lines:
        return content
    filtered = refiner(lines)
    return "\n".join(json.dumps(l, ensure_ascii=False) for l in filtered)


def clean_jsonl_file(input_path: str, output_path: str) -> int:
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
