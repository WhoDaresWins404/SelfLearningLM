SEED_CONTAINERS = [
    {
        "name": "Detailed Technical Documentation",
        "description": "Code snippets, function descriptions, API docs, and technical references with structured parameters",
        "schema_def": {
            "fields": [
                {"name": "title", "type": "string", "description": "Page or section title", "selector": "h1", "selector_type": "css", "required": True},
                {"name": "headings", "type": "array", "description": "Section headings (h1-h6)", "selector": "h1, h2, h3, h4, h5, h6", "selector_type": "css", "required": False},
                {"name": "code_blocks", "type": "array", "description": "Inline code and preformatted blocks", "selector": "code, pre, tt", "selector_type": "css", "required": False},
                {"name": "parameters", "type": "array", "description": "Function/method parameters and descriptions", "selector": "param, .param, .parameter", "selector_type": "css", "required": False},
            ]
        },
        "extractors": '{"title": "css:h1::text", "headings": "css:h1,h2,h3::text", "code_blocks": "css:code::text", "parameters": "css:.param::text"}'
    },
    {
        "name": "Forum Posts and Discussions",
        "description": "User comments, threads, discussions with author metadata and timestamps",
        "schema_def": {
            "fields": [
                {"name": "title", "type": "string", "description": "Thread or post title", "selector": "h1, .post-title, .thread-title", "selector_type": "css", "required": True},
                {"name": "author", "type": "string", "description": "Post author username", "selector": ".username, .author, .post-author", "selector_type": "css", "required": False},
                {"name": "timestamp", "type": "string", "description": "Post date/time", "selector": "time, .date, .post-date", "selector_type": "css", "required": False},
                {"name": "content", "type": "string", "description": "Post body text", "selector": ".post-content, .message, .post-body", "selector_type": "css", "required": True},
                {"name": "code_snippets", "type": "array", "description": "Code blocks within the post", "selector": "code, pre", "selector_type": "css", "required": False},
            ]
        },
        "extractors": '{"title": "css:h1::text", "author": "css:.username::text", "timestamp": "css:time::attr(datetime)", "content": "css:.post-content::text", "code_snippets": "css:code::text"}'
    },
    {
        "name": "Malformed or Obfuscated Code Snippets",
        "description": "Minified, encoded, or obfuscated JavaScript and HTML with detection metadata",
        "schema_def": {
            "fields": [
                {"name": "raw_script", "type": "string", "description": "Raw obfuscated script content", "selector": "script", "selector_type": "css", "required": True},
                {"name": "decoded_payload", "type": "string", "description": "Deobfuscated/decoded content", "selector": "", "selector_type": "css", "required": False},
                {"name": "technique", "type": "string", "description": "Obfuscation technique used (eval, base64, hex, etc)", "selector": "", "selector_type": "css", "required": False},
                {"name": "suspicious_indicators", "type": "array", "description": "Markers like data-malformed, obfuscated classes", "selector": "[data-malformed], .obfuscated, .bad", "selector_type": "css", "required": False},
            ]
        },
        "extractors": '{"raw_script": "css:script::text", "decoded_payload": "", "technique": "", "suspicious_indicators": "css:[data-malformed]::attr(class)"}'
    },
    {
        "name": "Dynamic Content (AJAX Calls)",
        "description": "API endpoints, JSON payloads, async-loaded content via fetch/XHR",
        "schema_def": {
            "fields": [
                {"name": "endpoint", "type": "string", "description": "API endpoint URL", "selector": "script", "selector_type": "css", "required": True},
                {"name": "method", "type": "string", "description": "HTTP method (GET, POST, etc)", "selector": "", "selector_type": "css", "required": False},
                {"name": "payload", "type": "object", "description": "Request/response payload structure", "selector": "", "selector_type": "css", "required": False},
                {"name": "trigger_event", "type": "string", "description": "Event that triggers the AJAX call (click, scroll, load)", "selector": "", "selector_type": "css", "required": False},
            ]
        },
        "extractors": '{"endpoint": "css:script::text", "method": "", "payload": "", "trigger_event": ""}'
    },
    {
        "name": "Hidden Data (CSS/JS Obfuscation)",
        "description": "Data concealed in CSS pseudo-elements, base64 encoding, style attributes, or invisible elements",
        "schema_def": {
            "fields": [
                {"name": "encoded_data", "type": "string", "description": "Raw encoded/hidden content", "selector": "style, [style]", "selector_type": "css", "required": True},
                {"name": "decoded_data", "type": "string", "description": "Decoded/unhidden content", "selector": "", "selector_type": "css", "required": False},
                {"name": "technique", "type": "string", "description": "Hiding technique (base64, css-keyframes, pseudo-element, display-none)", "selector": "", "selector_type": "css", "required": False},
                {"name": "selector", "type": "string", "description": "CSS selector where hidden data was found", "selector": "", "selector_type": "css", "required": False},
            ]
        },
        "extractors": '{"encoded_data": "css:style::text", "decoded_data": "", "technique": "", "selector": ""}'
    }
]
