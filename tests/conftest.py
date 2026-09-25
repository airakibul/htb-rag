"""Shared test fixtures for HTB RAG pipeline tests."""

from pathlib import Path
import pytest


@pytest.fixture
def sample_writeup_normal(tmp_path: Path) -> Path:
    """A well-formed HTB writeup with ## and ### headings."""
    content = '''# HTB - TestBox

## Box Info

| OS | Difficulty |
|----|------------|
| Linux | Medium |

## Recon

### Nmap Scan

```bash
nmap -sC -sV 10.10.10.1
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2
80/tcp open  http    Apache 2.4
```

Found open ports 22 and 80. The web server is running Apache.

### Web Enumeration

Used gobuster to find hidden directories:

```bash
gobuster dir -u http://10.10.10.1 -w /usr/share/wordlists/common.txt
/admin   (Status: 200)
/upload  (Status: 302)
```

## Foothold

### SQL Injection

Found SQLi in the login form using sqlmap:

```bash
sqlmap -u "http://10.10.10.1/login" --data="user=admin&pass=test" --dump
```

Got credentials: admin:s3cret_p@ss

## Privilege Escalation

### SUID Binary Abuse

Found a SUID binary:

```bash
find / -perm -4000 2>/dev/null
/usr/bin/custom_tool
```

Used GTFOBins technique to escalate to root.
'''
    md_file = tmp_path / "htb-testbox.md"
    md_file.write_text(content, encoding="utf-8")
    return md_file


@pytest.fixture
def sample_writeup_stub(tmp_path: Path) -> Path:
    """A very short writeup (stub file, <500 words)."""
    content = "# HTB - TinyBox\n\n## Recon\n\nRan nmap. Found port 80 open.\n\n## Foothold\n\nUsed default creds."
    md_file = tmp_path / "htb-tinybox.md"
    md_file.write_text(content, encoding="utf-8")
    return md_file


@pytest.fixture
def sample_writeup_stuck_headings(tmp_path: Path) -> Path:
    """A writeup with stuck headings (no newline before ##)."""
    content = (
        "# HTB - StuckBox\n\n"
        "Some intro text about the machine.18d 22:54:36 Creator ## Recon\n"
        "Did some scanning. Nmap revealed port 22 and port 80 are open on the target box.\n\n"
        "## Foothold\n"
        "Got shell via exploit. Exploited vulnerable service with custom python script to gain initial user access."
    )
    md_file = tmp_path / "htb-stuckbox.md"
    md_file.write_text(content, encoding="utf-8")
    return md_file



@pytest.fixture
def sample_chunks() -> list[dict]:
    """Pre-built chunk dicts for retriever/graph tests."""
    return [
        {
            "text": "[Machine: TestBox | OS: Linux | Phase: Recon | Path: Recon > Nmap Scan]\n\nnmap scan results...",
            "source": "htb-testbox",
            "machine_name": "TestBox",
            "os": "linux",
            "difficulty": "medium",
            "h2": "Recon",
            "h3": "Nmap Scan",
            "h4": "",
            "breadcrumb": "Recon > Nmap Scan",
            "chunk_type": "text",
            "has_cve": False,
            "cve_ids": [],
            "tools_mentioned": ["nmap"],
            "has_code": True,
            "attack_phase": "recon",
            "stub_file": False,
        },
        {
            "text": "[Machine: WinBox | OS: Windows | Phase: Privesc | Path: Privilege Escalation > DCSync]\n\nUsed secretsdump.py for dcsync ds-replication...",
            "source": "htb-winbox",
            "machine_name": "WinBox",
            "os": "windows",
            "difficulty": "hard",
            "h2": "Privilege Escalation",
            "h3": "DCSync",
            "h4": "",
            "breadcrumb": "Privilege Escalation > DCSync",
            "chunk_type": "text",
            "has_cve": False,
            "cve_ids": [],
            "tools_mentioned": ["secretsdump"],
            "has_code": True,
            "attack_phase": "privesc",
            "stub_file": False,
        },
    ]
