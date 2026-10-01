"""Unit tests for synthesizer.py."""

from src.pipeline.synthesizer import _clean_response, format_context


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


def test_format_context_injects_manifest_table():
    retrieval_result = {
        "chunks": [
            {
                "text": "Exploit instructions here.",
                "metadata": {"source": "htb-active", "breadcrumb": "Privesc > Kerberoast"},
            }
        ],
        "graph": {},
        "manifest": [
            {"machine": "htb-active", "os": "windows", "techniques": ["Kerberoasting"]},
            {"machine": "htb-forest", "os": "windows", "techniques": ["AS-REP Roast"]},
        ],
    }
    context = format_context(retrieval_result)
    assert "=== Complete Machine Manifest (Graph-Verified) ===" in context
    assert "| Machine | OS | Techniques |" in context
    assert "| htb-active | windows | Kerberoasting |" in context
    assert "| htb-forest | windows | AS-REP Roast |" in context


def test_format_context_retrieval_result_object():
    from src.domain.models import RetrievalResult

    result_obj = RetrievalResult(
        chunks=[{"text": "Some text", "metadata": {"source": "htb-box"}}],
        manifest=[{"machine": "htb-box", "os": "linux", "techniques": ["SUID / GTFOBins"]}],
    )
    context = format_context(result_obj)
    assert "=== Complete Machine Manifest (Graph-Verified) ===" in context
    assert "| htb-box | linux | SUID / GTFOBins |" in context


def test_system_prompt_manifest_rule():
    from src.pipeline.synthesizer import SYSTEM_PROMPT

    assert "Complete Machine Manifest" in SYSTEM_PROMPT
    assert "## Also Demonstrated On" in SYSTEM_PROMPT
    assert "Also demonstrated on: MachineA, MachineB, MachineC (technique-name)" in SYSTEM_PROMPT

