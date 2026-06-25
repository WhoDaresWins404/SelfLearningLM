from backend.processor.extractors.technical_doc import extract_technical_doc
from backend.processor.extractors.forum_post import extract_forum_post
from backend.processor.extractors.obfuscated_code import extract_obfuscated_code
from backend.processor.extractors.dynamic_content import extract_dynamic_content
from backend.processor.extractors.hidden_data import extract_hidden_data

EXTRACTORS = {
    "Technical Documentation": extract_technical_doc,
    "Forum Posts and Discussions": extract_forum_post,
    "Malformed or Obfuscated Code Snippets": extract_obfuscated_code,
    "Dynamic Content (AJAX Calls)": extract_dynamic_content,
    "Hidden Data (CSS/JS Obfuscation)": extract_hidden_data,
}


def extract(container_name: str, html: str) -> dict:
    extractor = EXTRACTORS.get(container_name)
    if not extractor:
        return {}
    return extractor(html)
