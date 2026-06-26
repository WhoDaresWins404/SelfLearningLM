def format_plain_text(content: dict) -> str:
    parts = []
    if content.get("title"):
        parts.append(f"# {content['title']}\n")
    if content.get("clean_text"):
        parts.append(content["clean_text"])
    if content.get("code_blocks"):
        parts.append("\n## Code\n")
        for cb in content["code_blocks"]:
            parts.append(f"```\n{cb}\n```")
    return "\n\n".join(parts)


def format_instruction_response(content: dict) -> str:
    lines = []
    sections = content.get("sections", [])
    for sec in sections:
        heading = sec.get("heading", "")
        paras = sec.get("paragraphs", [])
        if heading:
            instruction = heading
            if paras:
                response = "\n".join(paras)
                lines.append(jsonl_entry(instruction, response))
            elif len(paras) > 1:
                instruction = paras[0]
                response = "\n".join(paras[1:])
                lines.append(jsonl_entry(instruction, response))
        elif paras:
            for i in range(0, len(paras) - 1, 2):
                lines.append(jsonl_entry(paras[i], paras[i + 1] if i + 1 < len(paras) else ""))
    return "\n".join(lines)


def format_code_explanation(content: dict) -> str:
    lines = []
    sections = content.get("sections", [])
    for sec in sections:
        paras = sec.get("paragraphs", [])
        code_block = ""
        text_parts = []
        for p in paras:
            if p.startswith("```\n") and p.endswith("\n```"):
                if code_block and text_parts:
                    explanation = " ".join(text_parts)
                    lines.append(jsonl_entry(explanation, code_block))
                elif code_block:
                    lines.append(jsonl_entry("Code snippet", code_block))
                code_block = p[4:-4]
                text_parts = []
            else:
                text_parts.append(p)
        if code_block:
            explanation = " ".join(text_parts) if text_parts else "Code snippet"
            lines.append(jsonl_entry(explanation, code_block))
    return "\n".join(lines)


def format_qa(content: dict) -> str:
    lines = []
    sections = content.get("sections", [])
    for sec in sections:
        paras = sec.get("paragraphs", [])
        for i in range(len(paras) - 1):
            if paras[i].endswith("?"):
                lines.append(jsonl_entry(paras[i], paras[i + 1]))
    text = content.get("clean_text", "")
    import re
    for m in re.finditer(r"(?:^|\n)([^?\n]*\?)\s*\n((?:(?!\n[^?\n]*\?).)*)", text):
        lines.append(jsonl_entry(m.group(1).strip(), m.group(2).strip()))
    return "\n".join(lines)


def jsonl_entry(instruction: str, response: str) -> str:
    import json
    return json.dumps({"instruction": instruction, "response": response}, ensure_ascii=False)


FORMATTERS = {
    "plain_text": format_plain_text,
    "instruction_response": format_instruction_response,
    "code_explanation": format_code_explanation,
    "qa": format_qa,
}


def format_content(content: dict, fmt: str) -> str:
    formatter = FORMATTERS.get(fmt)
    if not formatter:
        return format_plain_text(content)
    return formatter(content)
