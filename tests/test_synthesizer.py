"""Unit tests for synthesizer.py."""

from src.synthesizer import _clean_response, format_context


def test_clean_response_strips_think_tags():
    raw = "<think>internal reasoning steps</think>Answer"
    cleaned = _clean_response(raw)
    assert cleaned == "Answer"


def test_clean_response_fixes_unclosed_fence():
    unclosed = "Here is the exploit command:\n```bash\nsqlmap -u http://target"
    cleaned = _clean_response(unclosed)
    assert cleaned.count("```") % 2 == 0
    assert cleaned.endswith("```")


def test_clean_response_empty():
    assert _clean_response("") == ""


def test_format_context_basic():
    retrieval_result = {
        "chunks": [
            {
                "text": "Sample chunk content for testing.",
                "metadata": {"source": "htb-test", "breadcrumb": "Recon > Nmap"},
            }
        ],
        "graph": {},
    }
    context = format_context(retrieval_result)
    assert "htb-test" in context
    assert "Sample chunk content for testing." in context
