import json
import re


def _est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _count_qa_pairs(text: str) -> int:
    return len(re.findall(r"[^?\n]*\?", text))


def _has_title(text: str) -> bool:
    lines = text.strip().split("\n")
    return bool(lines and len(lines[0].strip()) > 10 and len(lines[0].strip()) < 200)


def _detect_flags(rec: dict) -> list[str]:
    flags = []
    wc = rec.get("word_count", 0)
    if wc < 50:
        flags.append("too_short")
    if wc > 50000:
        flags.append("too_long")
    if not rec.get("source_url") and not rec.get("domain"):
        flags.append("no_metadata")
    if not rec.get("clean_text") and not rec.get("content"):
        flags.append("empty_content")
    if rec.get("quality_score", 0) < 20:
        flags.append("low_quality")
    return flags


def analyze_training_row(row: dict) -> dict:
    fmt = row.get("format", "")
    raw = row.get("content", "")
    source_url = row.get("source_url", "")
    domain = row.get("domain", "")

    word_count = 0
    char_count = len(raw)
    has_title = 0
    has_code = 0
    has_qa = 0
    section_count = 0
    has_instruction = 0
    has_response = 0
    line_count = 0

    try:
        parsed = json.loads(raw) if raw.startswith("{") else None
    except json.JSONDecodeError:
        parsed = None

    if fmt in ("instruction_response", "code_explanation", "qa"):
        if isinstance(parsed, dict) and "instruction" in parsed and "response" in parsed:
            has_instruction = 1
            has_response = 1
            word_count = len(parsed["instruction"].split()) + len(parsed["response"].split())
            line_count = 1
            if parsed.get("response", "").startswith("```"):
                has_code = 1
        elif isinstance(parsed, list):
            line_count = len(parsed)
            for item in parsed:
                if isinstance(item, dict):
                    if item.get("instruction"):
                        has_instruction = 1
                    if item.get("response"):
                        has_response = 1
                    combined = item.get("instruction", "") + " " + item.get("response", "")
                    word_count += len(combined.split())
                    if "```" in item.get("response", ""):
                        has_code = 1
        else:
            word_count = len(raw.split())
            has_title = 1 if _has_title(raw) else 0
            has_qa = _count_qa_pairs(raw)
    elif fmt == "plain_text" or not fmt:
        word_count = len(raw.split())
        has_title = 1 if _has_title(raw) else 0
        if "```" in raw:
            has_code = 1
        has_qa = _count_qa_pairs(raw)
        section_count = raw.count("\n## ") + raw.count("\n# ")
    else:
        word_count = len(raw.split())
        has_title = 1 if _has_title(raw) else 0
        if "```" in raw:
            has_code = 1

    quality = 30.0
    if word_count > 200:
        quality += 20
    if word_count > 500:
        quality += 10
    if has_title:
        quality += 10
    if has_code:
        quality += 15
    if has_qa >= 3:
        quality += 15
    elif has_qa >= 1:
        quality += 5
    if fmt in ("instruction_response", "code_explanation", "qa"):
        quality += 10
    if has_instruction and has_response:
        quality += 10
    if source_url or domain:
        quality += 5
    quality = min(100.0, round(quality, 1))

    is_reformattable = 0
    if fmt == "plain_text" and has_code:
        is_reformattable = 1
    elif fmt == "plain_text" and has_qa >= 3:
        is_reformattable = 1

    flags = _detect_flags({
        "word_count": word_count,
        "quality_score": quality,
        "source_url": source_url,
        "domain": domain,
        "content": raw,
        "clean_text": raw,
    })

    return {
        "format": fmt,
        "content_sample": raw[:200],
        "word_count": word_count,
        "char_count": char_count,
        "est_token_count": _est_tokens(raw),
        "has_title": has_title,
        "has_code": has_code,
        "has_qa": has_qa,
        "section_count": section_count,
        "has_instruction": has_instruction,
        "has_response": has_response,
        "line_count": line_count,
        "quality_score": quality,
        "is_reformattable": is_reformattable,
        "flags": json.dumps(flags),
    }


def analyze_formatted_line(item: dict) -> dict:
    instruction = item.get("instruction", "")
    response = item.get("response", "")
    combined = instruction + " " + response
    word_count = len(combined.split())
    char_count = len(combined)
    has_code = 1 if "```" in response else 0
    has_instruction = 1 if instruction else 0
    has_response = 1 if response else 0
    has_qa = 1 if instruction.strip().endswith("?") else 0
    has_title = 0

    quality = 30.0
    if word_count > 200:
        quality += 20
    if word_count > 500:
        quality += 10
    if has_code:
        quality += 15
    if has_instruction and has_response:
        quality += 10
    if has_qa:
        quality += 10
    quality = min(100.0, round(quality, 1))

    is_reformattable = 0
    if not has_instruction or not has_response:
        is_reformattable = 1

    flags = []
    if word_count < 20:
        flags.append("too_short")
    if not instruction:
        flags.append("no_instruction")
    if not response:
        flags.append("no_response")
    if not has_response and not has_instruction:
        flags.append("empty_entry")

    return {
        "format": "formatted",
        "content_sample": combined[:200],
        "word_count": word_count,
        "char_count": char_count,
        "est_token_count": _est_tokens(combined),
        "has_title": has_title,
        "has_code": has_code,
        "has_qa": has_qa,
        "section_count": 0,
        "has_instruction": has_instruction,
        "has_response": has_response,
        "line_count": 1,
        "quality_score": quality,
        "is_reformattable": is_reformattable,
        "flags": json.dumps(flags),
    }


def analyze_jsonl(file_content: str, filename: str) -> dict:
    lines = [l for l in file_content.split("\n") if l.strip()]
    results = []
    batch_summary = {
        "filename": filename,
        "total_records": len(lines),
        "high_value": 0,
        "reformattable": 0,
        "scores": [],
    }

    for i, line in enumerate(lines):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(obj, dict):
            if "format" in obj and "content" in obj:
                analysis = analyze_training_row(obj)
            elif "instruction" in obj:
                analysis = analyze_formatted_line(obj)
            else:
                word_count = len(str(obj).split())
                analysis = {
                    "format": "unknown",
                    "content_sample": str(obj)[:200],
                    "word_count": word_count,
                    "char_count": len(str(obj)),
                    "est_token_count": _est_tokens(str(obj)),
                    "has_title": 0, "has_code": 0, "has_qa": 0, "section_count": 0,
                    "has_instruction": 0, "has_response": 0, "line_count": 1,
                    "quality_score": min(100.0, round(word_count / 10, 1)),
                    "is_reformattable": 0,
                    "flags": json.dumps(["too_short"] if word_count < 20 else []),
                }

            analysis["record_index"] = i
            results.append(analysis)

            if analysis["quality_score"] >= 70:
                batch_summary["high_value"] += 1
            if analysis["is_reformattable"]:
                batch_summary["reformattable"] += 1
            batch_summary["scores"].append(analysis["quality_score"])

    batch_summary["avg_quality"] = round(
        sum(batch_summary["scores"]) / len(batch_summary["scores"]), 1
    ) if batch_summary["scores"] else 0.0
    batch_summary["total_records"] = len(results)

    high_pct = round(batch_summary["high_value"] / max(1, batch_summary["total_records"]) * 100)
    reformat_pct = round(batch_summary["reformattable"] / max(1, batch_summary["total_records"]) * 100)
    batch_summary["summary"] = (
        f"Imported {batch_summary['total_records']} records from '{filename}'. "
        f"Average quality score: {batch_summary['avg_quality']}/100. "
        f"{batch_summary['high_value']} ({high_pct}%) are high-value (score >= 70). "
        f"{batch_summary['reformattable']} ({reformat_pct}%) could be reformatted for higher training value. "
        f"Recommended for LM/LLM training: {batch_summary['high_value']} high-value records"
        + (f" + {batch_summary['reformattable']} reformattable records." if batch_summary['reformattable'] else ".")
    )

    return {"results": results, "summary": batch_summary}
