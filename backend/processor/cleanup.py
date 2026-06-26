import json
import re


def clean_code_text(text: str) -> str:
    """Fix unnatural spacing inside code blocks."""
    text = re.sub(r'\s+([\(\[\{])', r'\1', text)
    text = re.sub(r'([\)\]\}])\s+', r'\1', text)
    text = re.sub(r'\s*([.,;])\s*', r'\1 ', text)
    return text.strip()


def clean_prose(text: str) -> str:
    """Fix glued words in prose text."""
    if not text:
        return text
    text = re.sub(r'([\)\]\}])([a-z])', r'\1 \2', text)
    text = re.sub(r'([a-z])([\[\(\{])', r'\1 \2', text)
    text = re.sub(r'(\b\w+)(and|or|of|in|to|for|with|the|is|as|at|by|on|a)(\w+\b)', lambda m: m.group(1) + m.group(2) + ' ' + m.group(3) if m.group(2) in ('and', 'or', 'of', 'in', 'to', 'for', 'with', 'the', 'is', 'as', 'at', 'by', 'on', 'a') and len(m.group(1)) > 1 and len(m.group(3)) > 1 else m.group(0), text)
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
            cleaned.append(clean_code_text(part))
        else:
            cleaned.append(clean_prose(part))
    return "".join(cleaned)


def clean_sections(sections: list[dict]) -> list[dict]:
    """Clean all paragraph text within sections."""
    for sec in sections:
        cleaned_paras = []
        for p in sec.get("paragraphs", []):
            if p.startswith("```") and p.endswith("```") or p.startswith("> ") or p.startswith("- "):
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
