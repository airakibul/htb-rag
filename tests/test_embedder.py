"""Unit tests for embedder.py utility functions."""

from src.embedder import _chunk_id, _serialize_metadata, is_decorative_image


def test_serialize_metadata_lists_to_strings():
    chunk = {
        "source": "htb-testbox",
        "cve_ids": ["CVE-2021-44228", "CVE-2017-0143"],
        "tools_mentioned": ["nmap", "sqlmap"],
        "os": "linux",
        "has_cve": True,
    }
    meta = _serialize_metadata(chunk)

    assert meta["cve_ids"] == "CVE-2021-44228, CVE-2017-0143"
    assert meta["tools_mentioned"] == "nmap, sqlmap"
    assert meta["os"] == "linux"
    assert meta["has_cve"] is True


def test_chunk_id_deterministic():
    chunk = {
        "source": "htb-box",
        "h2": "Recon",
        "h3": "Nmap",
        "h4": "",
        "text": "Detailed scan output of ports 22 and 80.",
    }
    id1 = _chunk_id(chunk)
    id2 = _chunk_id(chunk)
    assert id1 == id2
    assert id1.startswith("htb-box__Recon__Nmap____")


def test_chunk_id_unique():
    chunk1 = {
        "source": "htb-box",
        "h2": "Recon",
        "h3": "Nmap",
        "h4": "",
        "text": "Detailed scan output of ports 22 and 80.",
    }
    chunk2 = {
        "source": "htb-box",
        "h2": "Recon",
        "h3": "Nmap",
        "h4": "",
        "text": "Detailed scan output of ports 443 and 8080.",
    }
    assert _chunk_id(chunk1) != _chunk_id(chunk2)


def test_is_decorative_image():
    # Decorative icons/banners (matching _DECORATIVE_PATTERNS: "cover", "-diff.", "-radar.", "/icons/", "box-")
    assert is_decorative_image("https://example.com/images/cover.jpg") is True
    assert is_decorative_image("https://example.com/icons/badge.svg") is True
    assert is_decorative_image("https://example.com/images/box-preview.png") is True
    assert is_decorative_image("https://example.com/stats-radar.png") is True

    # Real screenshots
    assert is_decorative_image("https://example.com/uploads/burp_sqli_evidence.png") is False
    assert is_decorative_image("https://example.com/writeup_assets/nmap_scan_output.png") is False

