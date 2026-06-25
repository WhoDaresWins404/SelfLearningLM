import pytest

from backend.processor.analyzer import analyze_blob
from backend.processor.extractors.technical_doc import extract_technical_doc
from backend.processor.extractors.forum_post import extract_forum_post
from backend.processor.extractors.obfuscated_code import extract_obfuscated_code
from backend.processor.extractors.dynamic_content import extract_dynamic_content
from backend.processor.extractors.hidden_data import extract_hidden_data
from backend.processor.qualifier import score
from backend.processor.refiner import refine


class TestAnalyzer:
    def test_technical_doc_detected(self):
        html = "<html><h1>API Reference</h1><pre>def foo(): pass</pre><code>bar</code></html>"
        matches = analyze_blob(html)
        assert "Technical Documentation" in matches

    def test_forum_detected(self):
        html = '<html><article><div class="post"><span class="username">user</span>content</div></article></html>'
        matches = analyze_blob(html)
        assert "Forum Posts and Discussions" in matches

    def test_obfuscation_detected(self):
        html = '<html><script>eval("alert(1)")</script></html>'
        matches = analyze_blob(html)
        assert "Malformed or Obfuscated Code Snippets" in matches


class TestExtractors:
    def test_technical_doc(self):
        html = "<html><h1>Title</h1><h2>Section</h2><code>fn()</code><p class=\"param\">x: int</p></html>"
        result = extract_technical_doc(html)
        assert result["title"] == "Title"
        assert "Section" in result["headings"]
        assert "fn()" in result["code_blocks"]
        assert "x: int" in result["parameters"]

    def test_forum_post(self):
        html = '<html><h1>Thread</h1><span class="username">alice</span><time datetime="2024-01-01">Jan</time><div class="post-content">Hello world</div><code>print(1)</code></html>'
        result = extract_forum_post(html)
        assert result["title"] == "Thread"
        assert result["author"] == "alice"

    def test_obfuscated_code(self):
        result = extract_obfuscated_code('<html><script>eval(String.fromCharCode(65))</script></html>')
        assert result["technique"] in ("eval", "string-fromcharcode")

    def test_dynamic_content(self):
        result = extract_dynamic_content('<html><script>fetch("/api/data")</script></html>')
        assert "/api/data" in result["endpoint"]

    def test_hidden_data_css(self):
        result = extract_hidden_data('<html><style>@keyframes x { from {content: "hidden"} }</style></html>')
        assert result["technique"] == "css-keyframes"


class TestQualifier:
    def test_empty_scores_low(self):
        assert score({}) >= 50.0

    def test_full_data_scores_high(self):
        assert score({"title": "A" * 1000, "body": "B" * 1000}) >= 70.0


class TestRefiner:
    def test_cleans_html_entities(self):
        result = refine({"text": "hello &amp; world"})
        assert result["text"] == "hello & world"

    def test_normalizes_whitespace(self):
        result = refine({"text": "hello    world\n\nfoo"})
        assert result["text"] == "hello world foo"

    def test_handles_lists(self):
        result = refine({"items": ["a&amp;b", "c"]})
        assert result["items"] == ["a&b", "c"]
