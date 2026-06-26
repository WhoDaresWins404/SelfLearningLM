import json
import re
from pathlib import Path


# --- Load wordfixes dictionary ---
_WORDFIXES_PATH = Path(__file__).parent / "wordfixes.json"
_wordfixes = {"exact": {}, "split_patterns": [], "url_patterns": [], "hex_pattern": ""}
if _WORDFIXES_PATH.exists():
    try:
        _wordfixes = json.loads(_WORDFIXES_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass

_EXACT_FIXES = _wordfixes.get("exact", {})
_SPLIT_PATTERNS = _wordfixes.get("split_patterns", [])
_URL_PATTERNS = _wordfixes.get("url_patterns", [])
_HEX_PATTERN = _wordfixes.get("hex_pattern", "")

# Pre-compile URL patterns
_URL_REPLACEMENTS = []
for pat_str, repl in _URL_PATTERNS:
    try:
        _URL_REPLACEMENTS.append((re.compile(pat_str, re.IGNORECASE), repl))
    except re.error:
        pass

# Build sorted list for split-pattern matching (longest prefix/suffix first)
_SPLIT_PREFIXES = sorted(
    [(p[0][1:], p[1]) for p in _SPLIT_PATTERNS if p[0].startswith("^")],
    key=lambda x: -len(x[0]),
)
_SPLIT_SUFFIXES = sorted(
    [(p[0][1:], p[1]) for p in _SPLIT_PATTERNS if p[0].startswith("$")],
    key=lambda x: -len(x[0]),
)

# Common English words that should never be merged (short valid words)
_VALID_WORDS = {
    "a", "an", "in", "on", "at", "to", "of", "by", "for", "with", "from",
    "is", "it", "as", "be", "or", "and", "but", "not", "the", "are", "was",
    "were", "has", "had", "have", "do", "does", "did", "can", "may", "will",
    "all", "any", "each", "some", "more", "most", "few", "new", "old",
    "out", "off", "up", "down", "left", "right", "set", "get", "use",
    "one", "two", "three", "four", "five", "first", "second", "third",
    "no", "yes", "so", "if", "then", "else", "than", "that", "this",
    "these", "those", "which", "who", "whom", "what", "when", "where",
    "how", "why", "here", "there", "now", "then", "just", "also",
    "very", "too", "much", "many", "such", "only", "own", "same",
    "other", "another", "both", "each", "every", "few", "several",
    "next", "last", "previous", "following", "above", "below",
    "before", "after", "during", "within", "without", "through",
    "between", "among", "about", "against", "around", "under",
    "over", "before", "behind", "beyond", "into", "onto", "upon",
    "via", "per", "versus", "plus", "minus", "times", "divided",
    "data", "base", "file", "code", "text", "name", "type", "size",
    "mode", "link", "path", "root", "user", "group", "port", "host",
}

# Hex character detection
_HEX_CHARS = set("0123456789ABCDEFabcdef")


def fix_broken_words(text: str, custom_fixes: dict | None = None) -> str:
    if not text:
        return text

    result = text

    # 1. Apply exact dictionary fixes (highest priority)
    fixes = dict(_EXACT_FIXES)
    if custom_fixes:
        fixes.update(custom_fixes)
    for broken, fixed in fixes.items():
        result = result.replace(broken, fixed)

    # 2. Fix hex byte spacing: "4 C 8 B" -> "4C8B"
    if _HEX_PATTERN:
        hex_re = re.compile(_HEX_PATTERN)
        for _ in range(10):
            new = hex_re.sub(lambda m: "".join(m.groups()), result)
            if new == result:
                break
            result = new

    # 3. Fix URL spacing: "github. com" -> "github.com"
    for pat, repl in _URL_REPLACEMENTS:
        result = pat.sub(repl, result)

    # 4. Auto-detect split words using split_patterns
    words = result.split(" ")
    fixed_words = []
    i = 0
    while i < len(words):
        if i + 1 < len(words):
            t1 = words[i]
            t2 = words[i + 1]
            merged = t1 + t2

            # Check if this looks like a split word
            should_merge = False

            # Check prefix patterns: t1 is empty or t2 starts with known prefix
            for prefix_str, _ in _SPLIT_PREFIXES:
                if t2.lower().startswith(prefix_str) and len(t1) > 1:
                    should_merge = True
                    break

            # Check suffix patterns: t1 ends with known suffix
            if not should_merge:
                for suffix_str, _ in _SPLIT_SUFFIXES:
                    if t1.lower().endswith(suffix_str) and len(t2) > 1:
                        should_merge = True
                        break

            # Check if this looks like a mid-word split (both parts short, merged looks plausible)
            if not should_merge:
                t1_lower = t1.lower()
                t2_lower = t2.lower()
                if (len(t1) <= 5 and len(t2) <= 5
                        and t1_lower not in _VALID_WORDS
                        and t2_lower not in _VALID_WORDS
                        and len(merged) >= 4
                        and merged.lower() not in _VALID_WORDS):
                    should_merge = True

            if should_merge:
                fixed_words.append(merged)
                i += 2
                continue
        fixed_words.append(words[i])
        i += 1

    result = " ".join(fixed_words)

    return result


# --- Language groups for syntax-aware code reconstruction ---
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


def clean_content(text: str, custom_word_fixes: dict | None = None) -> str:
    parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
    cleaned = []
    for part in parts:
        if part.startswith('```') and part.endswith('```'):
            cleaned.append(reconstruct_code_block(part))
        else:
            part = clean_prose(part)
            part = fix_broken_words(part, custom_fixes=custom_word_fixes)
            cleaned.append(part)
    return "".join(cleaned)


def clean_sections(sections: list[dict], custom_word_fixes: dict | None = None) -> list[dict]:
    for sec in sections:
        cleaned_paras = []
        for p in sec.get("paragraphs", []):
            if p.startswith("> ") or p.startswith("- "):
                cleaned_paras.append(p)
            else:
                cleaned_paras.append(clean_content(p, custom_word_fixes=custom_word_fixes))
        sec["paragraphs"] = cleaned_paras
    return sections


# --- Format-specific refiners ---

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


def clean_jsonl_file(input_path: str, output_path: str, custom_word_fixes: dict | None = None) -> int:
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
                    record[key] = clean_content(val, custom_word_fixes=custom_word_fixes)
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count
